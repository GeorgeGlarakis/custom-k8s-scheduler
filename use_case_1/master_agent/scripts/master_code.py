from kubernetes import client, config, watch
import random
import redis
from redis.commands.json.path import Path
from redis.commands.search.field import TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import psycopg2
import time
import os
import logging
import math
import requests
import migration_job

# Initialize environmental variables
this_node = os.environ.get('NODE_NAME', "master")
scheduler_name = os.environ.get('SCHEDULER_NAME', "my-scheduler")

# Get available nodes
def get_nodes(v1_core):
    # nodes = v1_core.list_node(label_selector="role=worker")
    nodes = v1_core.list_node()
    node_names = [node.metadata.name for node in nodes.items]
    return node_names

def get_node_images(v1_core, node_name, logger):
    try:
        node = v1_core.list_node(field_selector=f"metadata.name={node_name}")

        images = node['status']['images']
        images_list = []
        for image in images:
            if len(image['names'])<2:
                continue
            full_image = image['names'][1].rsplit(":",1)
            size = image['sizeBytes']
            next_image = {
                'name' : full_image[0],
                'tag' : full_image[1],
                'size_mb' : "{0:.1f}".format(size/1000000.)
            }
            images_list.append(next_image)
        return images_list
    except Exception as e:
        logger.error(f"Error getting node images: {e}")
        return e
    
def get_code_image(code_id, conn, logger):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT image, tag FROM code WHERE id = {code_id};")
        code = cur.fetchone()
        cur.close()
        return code[0], code[1]
    except Exception as e:
        logger.error(f"Error getting code image: {e}")
        return e
    
def set_task(task, logger):
    try:
        task["status"] = "pending"
        node_r = wait_redis(logger, host=f'{task["node_name"]}-worker-redis-service')
        node_r.json().set(f"task:{task['task_id']}", Path.root_path(), task)
        node_r.lpush("pending_tasks", task["task_id"])
        logger.debug(f"[task-{task['task_id']}] Task set successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Error setting task: {e}")
        return False

def get_buffer_time(node_name, logger):
    try:
        node_r = wait_redis(logger, host=f'{node_name}-worker-redis-service')
        redis_init_index(node_r, logger)
        rs = node_r.ft("task:index")
        q = Query("@status:pending").return_fields("execution_time")
        pending_tasks = rs.search(q.paging(0, 10))

        total_results = pending_tasks.total
        buffer_time = 0
        offset = 0

        while offset < total_results:
            pending_tasks = rs.search(q.paging(offset, 10))

            for task in pending_tasks.docs:
                buffer_time += float(task["execution_time"])
            offset += 10
        return buffer_time

    except Exception as e:
        logger.error(f"Error calculating buffer time: {e}")
        return None
    
def get_execution_time(node_name, code_id, data_id, conn, logger):
    try:
        cpu_speed_devider = 1 # 1000000
        execution_time = 0
        cur = conn.cursor()
        cur.execute(f"""
            SELECT cpu_speed FROM node
            WHERE name = '{node_name}';""")
        cpu_speed = cur.fetchone()[0]
        logger.debug(f"[{node_name}] CPU Speed: {cpu_speed}")
        cur.execute(f"""
            SELECT complexity FROM code
            WHERE id = {code_id};""")
        complexity = cur.fetchone()[0]
        logger.debug(f"[code-{code_id}] Complexity: {complexity}")
        cur.execute(f"""
            SELECT count_n FROM data
            WHERE id = {data_id};""")
        count_n = cur.fetchone()[0]
        logger.debug(f"[data-{data_id}] Count: {count_n}")
        
        # O(n) | O(n^2) | O(n*log(n)) 
        case = complexity.lower()
        if case == "O(n)".lower():
            execution_time = count_n / ( cpu_speed * cpu_speed_devider )
        elif case == "O(n^2)".lower():
            execution_time = ( count_n ^ 2 ) / ( cpu_speed * cpu_speed_devider )
        elif case == "O(n*log(n))".lower():
            execution_time = ( count_n * math.log(count_n) ) / ( cpu_speed * cpu_speed_devider )
        else:
            logger.error(f"[code-{code_id}] Unknown complexity: {complexity}")
            return None
        
        cur.close()        
        return execution_time
    
    except Exception as e:
        logger.error(f"Error calculating execution time: {e}")
        return None
    
def get_code_migration_time(node_id, code_id, conn, logger):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT size_mb FROM code WHERE id = {code_id};")
        code_size = cur.fetchone()[0]
        # cur.execute(f"SELECT latency_ms FROM node_latency WHERE node_from = 'master' AND node_to = {node_id};")
        # node_lat = cur.fetchone()[0]
        network_speed = 1  # Mbps

        get_code_migration_time = code_size / network_speed
        cur.close()
        return get_code_migration_time

    except Exception as e:
        logger.error(f"Error calculating code migration time: {e}")
        return None
    
def get_data_migration_time(node_from, node_to, data_id, conn, logger):
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT size_mb FROM data WHERE id = {data_id};")
        data_size = cur.fetchone()[0]
        cur.execute(f"""
                    SELECT latency_ms FROM node_latency 
                    WHERE node_from = {node_from}
                    AND node_to = {node_to};
                    """)
        node_latency = cur.fetchone()[0]
        network_speed = 1

        get_data_migration_time = ( data_size / network_speed ) + node_latency

        cur.close()
        return get_data_migration_time

    except Exception as e:
        logger.error(f"Error calculating data migration time: {e}")
        return None
    
def migrate_data(task_info, conn, logger):
    try:
        cur = conn.cursor()
        cur.execute(f"""
            SELECT n.name FROM node_info ni
            INNER JOIN node n ON ni.node_id = n.id
            INNER JOIN node_latency nl ON nl.node_from = ni.node_id
            WHERE ni.pod_type = 'data' AND ni.pod_id = {task_info['data_id']}
            AND nl.node_to IN (SELECT id FROM node WHERE name = '{task_info['node_name']}')
            ORDER BY nl.latency_ms ASC
            LIMIT 1;
            """)
        node_from = cur.fetchone()[0]

        url = f"http://{task_info["node_name"]}-worker-agent-service.default.svc.cluster.local:8080/api/v1/migrate_data"
        body = {
            "node_name": node_from,
            "data_id": task_info["data_id"]
        }
        response = requests.post(url, json=body)
        migrate_data = response.json()

        if 'error' in migrate_data:
            logger.error(f"[task-{task_info['task_id']}] Data migration failed: {migrate_data['error']}")
            return False

        # Copy data
        cur.execute(f"""
            INSERT INTO node_info (node_id, pod_id, pod_type)
            SELECT node.id, {task_info['data_id']}, 'data' FROM node
            WHERE name = '{task_info['node_name']}';
            """)
        
        # # Move data
        # cur.execute(f"""
        #     UPDATE node_info
        #     SET node_id = (SELECT id FROM node WHERE name = '{task_info['node_name']}')
        #     WHERE pod_id = {task_info['data_id']} AND pod_type = 'data';
        #     """)

        conn.commit()
        cur.close()
        return True
        
    except Exception as e:
        logger.error(f"[task-{task_info['task_id']}] Error migrating data: {e}")
        return False

    
def get_earliest_completion_time(task_info, conn, v1_core, logger):
    try:
        earliest_completion_time = None
        node_selection = None
        # Evaluate each node
        nodes = get_nodes(v1_core)

        node_info = {}

        cur = conn.cursor()
        for node in nodes:
            logger.debug(f"[task-{task_info['task_id']}] Evaluating node: {node}")

            # Check if node has code and data
            this_node_info = {"code_exists":False, "data_exists":False}
            cur.execute(f"""
                SELECT 1 FROM node_info
                INNER JOIN node ON node_info.node_id = node.id
                WHERE node_info.pod_type = 'code'
                AND node.name = '{node}'
                AND node_info.pod_id = {task_info['code_id']};""")
            code = cur.fetchone()
            logger.debug(f"[task-{task_info['task_id']}][{node}] Code: {code}")
            if code is not None:
                this_node_info["code_exists"] = True
        
            cur.execute(f"""
                SELECT 1 FROM node_info
                INNER JOIN node ON node_info.node_id = node.id
                WHERE node_info.pod_type = 'data'
                AND node.name = '{node}'
                AND node_info.pod_id = {task_info['data_id']};""")
            data = cur.fetchone()
            logger.debug(f"[task-{task_info['task_id']}][{node}] Data: {data}")
            if data is not None:
                this_node_info["data_exists"] = True

            cur.execute(f"SELECT id FROM node WHERE name = '{node}';")
            node_id = cur.fetchone()[0]
            logger.debug(f"[task-{task_info['task_id']}][{node}] Node ID: {node_id}")
            buffer_time = get_buffer_time(node, logger)
            logger.debug(f"[task-{task_info['task_id']}][{node}] Buffer Time: {buffer_time}")
            execution_time = get_execution_time(node, task_info['code_id'], task_info['data_id'], conn, logger)
            logger.debug(f"[task-{task_info['task_id']}][{node}] Execution Time: {execution_time}")
            
            if not this_node_info["code_exists"]:
                code_migration_time = get_code_migration_time(node_id, task_info['code_id'], conn, logger)
                logger.debug(f"[task-{task_info['task_id']}][{node}] Code Migration Time: {code_migration_time}")

            if not this_node_info["data_exists"]:
                cur.execute(f"""
                    SELECT n.id FROM node_info ni
                    INNER JOIN node n ON ni.node_id = n.id
                    INNER JOIN node_latency nl ON nl.node_from = ni.node_id
                    WHERE ni.pod_type = 'data' AND ni.pod_id = {task_info['data_id']}
                    AND nl.node_to IN (SELECT id FROM node WHERE name = '{node}')
                    ORDER BY nl.latency_ms ASC
                    LIMIT 1;
                    """)
                node_from = cur.fetchone()[0]
                data_migration_time = get_data_migration_time(node_from, node_id, task_info['data_id'], conn, logger)
                logger.debug(f"[task-{task_info['task_id']}][{node}] Data Migration Time: {data_migration_time}")

            if this_node_info["code_exists"] and this_node_info["data_exists"]:
                # Calculate Completion Time
                ## Buffer Time + Execution Time
                completion_time = float(buffer_time) + float(execution_time)
            elif this_node_info["code_exists"] and not this_node_info["data_exists"]:
                # Calculate Code Time
                ## Buffer Time + Data Migration Time + Execution Time
                completion_time = float(buffer_time) + float(execution_time) + float(data_migration_time)
            elif not this_node_info["code_exists"] and this_node_info["data_exists"]:
                # Calculate Data Time
                ## Buffer Time + Fetch Image + Execution Time
                completion_time = float(buffer_time) + float(execution_time) + float(code_migration_time)
            else:
                # Calculate Buffer Time
                ## Buffer Time + max( Fetch Image + Data Migration Time ) + Execution Time
                migration_time = max(code_migration_time, data_migration_time)
                completion_time = float(buffer_time) + float(execution_time) + float(migration_time)

            this_node_info["execution_time"] = execution_time
            this_node_info["completion_time"] = completion_time

            if earliest_completion_time is None or completion_time < earliest_completion_time:
                node_selection = node
                earliest_completion_time = completion_time

            node_info[node] = this_node_info

        cur.close()
        
        logger.debug(f"[task-{task_info['task_id']}] Node Selection: {node_selection}")
        task_info['node_name'] = node_selection
        logger.debug(f"[task-{task_info['task_id']}] Execution Time: {execution_time}")
        task_info['execution_time'] = str(execution_time)
        logger.debug(f"[task-{task_info['task_id']}] Earliest Completion Time: {earliest_completion_time}")
        task_info['earliest_completion_time'] = str(earliest_completion_time)

        task_info['node_info'] = node_info
        return task_info
    
    except Exception as e:
        logger.error(f"[task-{task_info['task_id']}] Error evaluating task: {e}")
        return e
    
def get_fairness(task_info, conn, v1_core, logger):
    try:
        cur = conn.cursor()
        cur.execute(f"""SELECT name, used_cpu_cycles FROM node;""")
        nodes = cur.fetchall()

        node_name_flag = ""
        node_used_cycles_flag = -1
        for node in nodes:
            node_name = node[0]
            node_used_cycles = node[1]

            if node_used_cycles_flag == -1:
                node_name_flag = node_name
                node_used_cycles_flag = node_used_cycles
                continue
            
            if node_used_cycles < node_used_cycles_flag:
                node_name_flag = node_name
                node_used_cycles_flag = node_used_cycles

        cur.close()

        task_info = get_earliest_completion_time(task_info, conn, v1_core, logger)
        task_info['node_name'] = node_name_flag
        task_info['earliest_completion_time'] = task_info['node_info'][node_name_flag]["completion_time"]

        return task_info
    
    except Exception as e:
        logger.error(f"[task-{task_info['task_id']}] Error evaluating task: {e}")
        return e


def evaluate_task(task_info, conn, v1_core, logger):
    try:
        cur = conn.cursor()

        task_info["image"], task_info["tag"] = get_code_image(task_info["code_id"], conn, logger)

        if task_info["policy"] == "earliest":
            task_info = get_earliest_completion_time(task_info, conn, v1_core, logger)
        elif task_info["policy"] == "fairness":
            task_info = get_fairness(task_info, conn, v1_core, logger)
        else:
            return {'error':'unkown policy'}
        
        logger.debug(f"[task-{task_info['task_id']}]: {task_info}")
        
        if not task_info["node_info"][task_info["node_name"]]["data_exists"]:
            if not migrate_data(task_info, conn, logger):
                return {'error':'migrate_data() failed'}
            
        if not task_info["node_info"][task_info["node_name"]]["code_exists"]:
            cur.execute(f"""
                INSERT INTO node_info (node_id, pod_id, pod_type)
                SELECT node.id, {task_info['code_id']}, 'code' FROM node
                WHERE name = '{task_info['node_name']}';
                """)
            conn.commit()
        
        if set_task(task_info, logger):
            cur.execute(f"""
                UPDATE task 
                SET node_id = node.id
                    , time_scheduled=CURRENT_TIMESTAMP
                    , execution_prediction_ms = {task_info['execution_time']}
                    , completion_prediction_ms = {task_info['earliest_completion_time']}
                FROM node
                WHERE task.id = {task_info['task_id']}
                AND node.name = '{task_info['node_name']}';""")
            conn.commit()
            cur.close()
        else:
            return {'error':'set_task() failed'}

        return {'status':'scheduled'}
    
    except Exception as e:
        logger.error(f"[task-{task_info['task_id']}] Error evaluating task: {e}")
        return {'error':e}
    

def redis_init_index(r, logger):
    try:
        schema = (
            TextField("$.execution_time", as_name="execution_time"),
            TextField("$.status", as_name="status")
        )

        rs = r.ft("task:index")
        rs.create_index(schema, definition=IndexDefinition(prefix=['task:'], index_type=IndexType.JSON))
    
    except Exception as e:
        logger.error(f"Error redis_init: {e}")

    
def wait_redis(logger, host, port=6379, db=0, timeout=60, interval=5):
    start_time = time.time()
    r = redis.Redis(host=host, port=port, db=db)

    while True:
        try:
            # Attempt to ping the Redis server
            if r.ping():
                logger.info("Connected to Redis!")
                return r
        except redis.exceptions.ConnectionError:
            pass  # Redis server is not yet available

        # Check if the timeout has been exceeded
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            raise Exception(f"Redis service not available after {timeout} seconds.")

        logger.info(f"Waiting for Redis... ({elapsed_time:.1f}s elapsed)")
        time.sleep(interval)