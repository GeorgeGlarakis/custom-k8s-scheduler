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
def get_nodes():
    nodes = v1_core.list_node(label_selector="role=worker")
    node_names = [node.metadata.name for node in nodes.items]
    return node_names

# Evaluate most suitable node for deployment
def node_evaluation(pod):
    # Get list of nodes and randomly select one
    nodes = get_nodes()
    assigned_node = random.choice(nodes)
    logger.info(f"Assigning to node: {assigned_node}")

    ################################################################################
    # Data Migration Job
    # python3 migration_job.py --source_node 'node-m02' --destination_node 'node' --data_deployment_name 'data-1'

    # migration_object = {
    #     'source_node': "",
    #     'destination_node': "",
    #     'data_deployment_name': pod.metadata.labels['data_id']
    # }

    # migration_job.main(migration_object)

    ################################################################################

    # Assign the deployment to the selected node
    assign_to_node(pod, assigned_node)

def assign_to_node(pod, assigned_node):
    try:
        node_r = redis.Redis(host=f'{assigned_node}-redis-service', port=6379)
        pod_name = pod.metadata.name
        node_r.hset("pending_deployments", pod_name, pod.metadata.name)
        node_r.lpush("pending_tasks", pod_name)
    except Exception as e:
        logger.error(f"Error assigning pod to node {assigned_node}: {e}")

# Watch for new deployments and store for later execution
def watch_deployments():
    w = watch.Watch()
    for event in w.stream(v1_core.list_namespaced_pod, namespace="default"):
        if event['object'].status.phase == "Pending" and \
            event['type'] == "ADDED" and \
            event['object'].spec.scheduler_name == scheduler_name and \
            event['object'].metadata.labels.get('role') == "code":

            pod = event['object']
            pod_name = pod.metadata.name

            logger.info(f"New pending pod detected: {pod_name}")
            
            # Store deployment details in Redis (you can also serialize the deployment spec)
            r.hset("pending_deployments", pod_name, pod.metadata.name)
            logger.info(f"Deployment {pod_name} stored for later execution")

            node_evaluation(pod)

def get_node_images(v1_core, node_name):
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
    
def set_task(task):
    try:
        node_r = redis.Redis(host=f'{task["node_name"]}-redis-service', port=6379)
        node_r.lpush("pending_tasks", task["task_id"])
        node_r.json().set(f"task:{task["task_id"]}", Path.root_path(), task)
    
    except Exception as e:
        logger.error(f"Error setting task: {e}")
        return e

    
def get_buffer_time(node_name):
    try:
        node_r = redis.Redis(host=f'{node_name}-redis-service', port=6379)
        rs = node_r.ft("task:index")
        pending_tasks = rs.search(
            Query("@status:pending").return_fields("task_id", "execution_time")
        )

        buffer_time = 0
        for task in pending_tasks:
            buffer_time += task["execution_time"]

        return buffer_time

    except Exception as e:
        logger.error(f"Error evaluating task: {e}")
        return None
    
def get_execution_time(node_name, code_id, data_id, conn):
    try:
        cpu_speed = conn.execute("\
                        SELECT cpu_speed FROM node \
                        WHERE name = ?;", node_name).fetchone()[0]
        complexity = conn.execute("\
                        SELECT complexity FROM code \
                        WHERE id = ?;", code_id).fetchone()[0]
        count_n = conn.execute("\
                        SELECT count_n FROM data \
                        WHERE id = ?;", data_id).fetchone()[0]
        
        # O(n) | O(n^2) | O(nlogn)
        case = complexity.lower()
        if case == "O(n)":
            execution_time = count_n / (cpu_speed * 1000000)
        elif case == "O(n^2)":
            execution_time = ( count_n ^ 2 ) / ( cpu_speed * 1000000 )
        elif case == "O(nlogn)":
            execution_time = ( count_n * math.log(count_n) ) / ( cpu_speed * 1000000 )
        
        return execution_time
    
    except Exception as e:
        logger.error(f"Error calculating execution time: {e}")
        return None
    
def get_code_migration_time(node_id, code_id, conn):
    try:
        code_size = conn.execute(f"SELECT size_mb FROM code WHERE id = ?;", code_id).fetchone()[0]
        # node_lat = conn.execute(f"SELECT latency_ms FROM node_latency WHERE node_from = ? AND node_to = ?;", "master", node_id).fetchone()[0]
        network_speed = 1000 # Mbps

        get_code_migration_time = code_size / network_speed
        return get_code_migration_time

    except Exception as e:
        logger.error(f"Error calculating code migration time: {e}")
        return None
    
def get_data_migration_time(node_from, node_to, data_id, conn):
    try:
        data_size = conn.execute(f"SELECT size_mb FROM data WHERE id = ?;", data_id).fetchone()[0]
        node_latency = conn.execute(f"SELECT latency_ms FROM node_latency WHERE node_from = ? AND node_to = ?;", node_from, node_to).fetchone()[0]
        network_speed = 1000 # Mbps

        get_data_migration_time = ( data_size / network_speed ) + node_latency
        return get_data_migration_time

    except Exception as e:
        logger.error(f"Error calculating data migration time: {e}")
        return None
    
def evaluate_task(code_id, data_id):
    try:
        earliest_completion_time = None
        node_selection = None
        # Evaluate each node
        nodes = get_nodes()
        for node in nodes:
            # Check if node has code and data
            code_exists = False
            code = conn.execute("\
                        SELECT 1 FROM node_info \
                        INNER JOIN node ON node_info.node_id = node.id \
                        WHERE node_info.pod_type = 'code' \
                        AND node.name = ? \
                        AND node_info.pod_id = ?;", node, code_id).fetchone()
            if code is not None:
                code_exists = True

            data_exists = False           
            data = conn.execute("\
                        SELECT 1 FROM node_info \
                        INNER JOIN node ON node_info.node_id = node.id \
                        WHERE node_info.pod_type = 'data' \
                        AND node.name = ? \
                        AND node_info.pod_id = ?;", node, data_id).fetchone()
            if data is not None:
                data_exists = True

            node_id = conn.execute("SELECT id FROM node WHERE name = ?;", node).fetchone()[0]
            buffer_time = get_buffer_time(node)
            execution_time = get_execution_time(node, code_id, data_id, conn)
            code_migration_time = get_code_migration_time(node_id, code_id, conn)

            node_from = conn.execute("\
                                SELECT node_id FROM node_info \
                                WHERE pod_type = 'data' AND pod_id = ?;", data_id).fetchone()[0]
            data_migration_time = get_data_migration_time(node_from, node_id, data_id, conn)

            if code_exists and data_exists:
                # Calculate Completion Time
                ## Buffer Time + Execution Time
                completion_time = buffer_time + execution_time
            elif code_exists and not data_exists:
                # Calculate Code Time
                ## Buffer Time + Data Migration Time + Execution Time
                node_from = conn.execute("\
                                SELECT node_id FROM node_info \
                                WHERE pod_type = 'data' AND pod_id = ?;", data_id).fetchone()[0]
                completion_time = buffer_time + execution_time + data_migration_time
            elif not code_exists and data_exists:
                # Calculate Data Time
                ## Buffer Time + Fetch Image + Execution Time
                completion_time = buffer_time + execution_time + code_migration_time
            else:
                # Calculate Buffer Time
                ## Buffer Time + max( Fetch Image + Data Migration Time ) + Execution Time
                node_from = conn.execute("\
                                SELECT node_id FROM node_info \
                                WHERE pod_type = 'data' AND pod_id = ?;", data_id).fetchone()[0]
                migration_time = max(code_migration_time, data_migration_time)
                completion_time = buffer_time + execution_time + migration_time

            if earliest_completion_time is None or completion_time < earliest_completion_time:
                node_selection = node
                earliest_completion_time = completion_time
            
        return node_selection, execution_time
    
    except Exception as e:
        logger.error(f"Error evaluating task: {e}")
        return e

def redis_init(r):
    # task_info = {
    #     "task_id": "",
    #     "code_id": "",
    #     "data_id": "",
    #     "node_name": "",
    #     "execution_time": "",
    #     "status": "",
    #     "time_created": "",
    #     "time_completed": ""
    # }
    try:
        schema = (
            NumericField("$.task_id", as_name="task_id"),
            NumericField("$.code_id", as_name="code_id"),
            NumericField("$.data_id", as_name="data_id"),
            TextField("$.node_name", as_name="node_name"),
            NumericField("$.execution_time", as_name="execution_time"),
            TextField("$.status", as_name="status"),
            TextField("$.time_created", as_name="time_created"),
            TextField("$.time_completed", as_name="time_completed")
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
    redis = wait_redis(host=f'{this_node}-redis-service')
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

    logger.info("Starting master agent...")
    watch_deployments()