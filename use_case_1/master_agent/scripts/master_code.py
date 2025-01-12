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
        node_r = redis.Redis(host=f'{task["node_name"]}-worker-redis-service', port=6379)
        node_r.json().set(f"task:{task['task_id']}", Path.root_path(), task)
        node_r.lpush("pending_tasks", task["task_id"])
    
    except Exception as e:
        logger.error(f"Error setting task: {e}")
        return e

def get_buffer_time(node_name, logger):
    try:
        node_r = redis.Redis(host=f'{node_name}-worker-redis-service', port=6379)
        redis_init(node_r, logger)
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
        cur.execute(f"SELECT latency_ms FROM node_latency WHERE node_from = {node_from} AND node_to = {node_to};")
        node_latency = cur.fetchone()[0]
        network_speed = 1 # Mbps

        get_data_migration_time = ( data_size / network_speed ) + node_latency

        cur.close()
        return get_data_migration_time

    except Exception as e:
        logger.error(f"Error calculating data migration time: {e}")
        return None
    
def get_earliest_completion_time(task_info, conn, v1_core, logger):
    try:
        earliest_completion_time = None
        node_selection = None
        # Evaluate each node
        nodes = get_nodes(v1_core)

        cur = conn.cursor()
        for node in nodes:
            logger.debug(f"[task-{task_info['task_id']}] Evaluating node: {node}")

            # Check if node has code and data
            code_exists = False
            cur.execute(f"""
                SELECT 1 FROM node_info
                INNER JOIN node ON node_info.node_id = node.id
                WHERE node_info.pod_type = 'code'
                AND node.name = '{node}'
                AND node_info.pod_id = {task_info['code_id']};""")
            code = cur.fetchone()
            logger.debug(f"[task-{task_info['task_id']}][{node}] Code: {code}")
            if code is not None:
                code_exists = True

            data_exists = False           
            cur.execute(f"""
                SELECT 1 FROM node_info
                INNER JOIN node ON node_info.node_id = node.id
                WHERE node_info.pod_type = 'data'
                AND node.name = '{node}'
                AND node_info.pod_id = {task_info['data_id']};""")
            data = cur.fetchone()
            logger.debug(f"[task-{task_info['task_id']}][{node}] Data: {data}")
            if data is not None:
                data_exists = True

            cur.execute(f"SELECT id FROM node WHERE name = '{node}';")
            node_id = cur.fetchone()[0]
            logger.debug(f"[task-{task_info['task_id']}][{node}] Node ID: {node_id}")
            buffer_time = get_buffer_time(node, logger)
            logger.debug(f"[task-{task_info['task_id']}][{node}] Buffer Time: {buffer_time}")
            execution_time = get_execution_time(node, task_info['code_id'], task_info['data_id'], conn, logger)
            logger.debug(f"[task-{task_info['task_id']}][{node}] Execution Time: {execution_time}")
            
            if not code_exists:
                code_migration_time = get_code_migration_time(node_id, task_info['code_id'], conn, logger)
                logger.debug(f"[task-{task_info['task_id']}][{node}] Code Migration Time: {code_migration_time}")
            # buffer_time = 30
            # execution_time = 10
            # code_migration_time = 5

            if not data_exists:
                cur.execute(f"""
                    SELECT node_id FROM node_info
                    WHERE pod_type = 'data' AND pod_id = {task_info['data_id']};""")
                node_from = cur.fetchone()[0]
                data_migration_time = get_data_migration_time(node_from, node_id, task_info['data_id'], conn, logger)
                logger.debug(f"[task-{task_info['task_id']}][{node}] Data Migration Time: {data_migration_time}")

            if code_exists and data_exists:
                # Calculate Completion Time
                ## Buffer Time + Execution Time
                completion_time = float(buffer_time) + float(execution_time)
            elif code_exists and not data_exists:
                # Calculate Code Time
                ## Buffer Time + Data Migration Time + Execution Time
                cur.execute(f"""
                    SELECT node_id FROM node_info
                    WHERE pod_type = 'data' AND pod_id = {task_info['data_id']};""")
                node_from = cur.fetchone()[0]
                completion_time = float(buffer_time) + float(execution_time) + float(data_migration_time)
            elif not code_exists and data_exists:
                # Calculate Data Time
                ## Buffer Time + Fetch Image + Execution Time
                completion_time = float(buffer_time) + float(execution_time) + float(code_migration_time)
            else:
                # Calculate Buffer Time
                ## Buffer Time + max( Fetch Image + Data Migration Time ) + Execution Time
                cur.execute(f"""
                    SELECT node_id FROM node_info 
                    WHERE pod_type = 'data' AND pod_id = {task_info['data_id']};""")
                node_from = cur.fetchone()[0]
                migration_time = max(code_migration_time, data_migration_time)
                completion_time = float(buffer_time) + float(execution_time) + float(migration_time)

            if earliest_completion_time is None or completion_time < earliest_completion_time:
                node_selection = node
                earliest_completion_time = completion_time

        cur.close()
        
        logger.debug(f"[task-{task_info['task_id']}] Node Selection: {node_selection}")
        task_info['node_name'] = node_selection
        logger.debug(f"[task-{task_info['task_id']}] Execution Time: {execution_time}")
        task_info['execution_time'] = str(execution_time)
        logger.debug(f"[task-{task_info['task_id']}] Earliest Completion Time: {earliest_completion_time}")
        task_info['earliest_completion_time'] = str(earliest_completion_time)
        # task_info['node_name'] = 'node'
        # task_info['execution_time'] = 15
        # task_info['earliest_completion_time'] = 25
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

        return task_info
    
    except Exception as e:
        logger.error(f"[task-{task_info['task_id']}] Error evaluating task: {e}")
        return e




    

def redis_init(r, logger):
    try:
        schema = (
            # NumericField("$.task_id", as_name="task_id"),
            # NumericField("$.code_id", as_name="code_id"),
            # NumericField("$.data_id", as_name="data_id"),
            # TextField("$.node_name", as_name="node_name"),
            TextField("$.execution_time", as_name="execution_time"),
            TextField("$.status", as_name="status"),
            # TextField("$.time_created", as_name="time_created"),
            # TextField("$.time_completed", as_name="time_completed")
        )

        rs = r.ft("task:index")
        rs.create_index(schema, definition=IndexDefinition(prefix=['task:'], index_type=IndexType.JSON))
    
    except Exception as e:
        logger.error(f"Error redis_init: {e}")

    
def wait_redis(host, port=6379, db=0, timeout=60, interval=5):
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

if __name__ == "__main__":
    # Load Kubernetes configuration
    # config.load_kube_config() ## <-- for debugging, running outside the cluster
    config.load_incluster_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='master_agent_logfile.log', encoding='utf-8', level=logging.DEBUG)

    # Initialize Redis (or use any other store)
    redis = wait_redis(host=f'{this_node}-master-redis-service')
    redis_init(redis)

    # Initialize Postgres
    conn = psycopg2.connect(
        host =     os.environ.get('POSTGRES_HOST', 'postgres.default.svc.cluster.local'),
        port =     os.environ.get('POSTGRES_PORT', 5432),
        database = os.environ.get('POSTGRES_DB', 'master_db'),
        user =     os.environ.get('POSTGRES_USER', 'master_agent'),
        password = os.environ.get('POSTGRES_PASSWORD', 'master_password')
    )

    # Set up Kubernetes API client
    v1_apps = client.AppsV1Api()
    v1_core = client.CoreV1Api()
    v1_batch = client.BatchV1Api()