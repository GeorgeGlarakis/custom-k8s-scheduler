from kubernetes import client, config
import redis
import time
import json
import os
import logging

# Load Kubernetes configuration
# config.load_kube_config() ## <-- for debugging, running outside the cluster
config.load_incluster_config()

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

# Set up Kubernetes API client
v1_apps = client.AppsV1Api()
v1_core = client.CoreV1Api()

# Initialize environmental variables
node_name = os.environ.get('NODE_NAME') 

def scheduler(pod_name, node_name, namespace="default"):    
    target = client.V1ObjectReference(api_version='v1', kind='Node', name=node_name, namespace=namespace)

    meta=client.V1ObjectMeta()
    meta.name=pod_name

    body=client.V1Binding(target=target, metadata=meta) # V1Binding is deprecated

    # event_response = create_scheduled_event(name, node, namespace, scheduler_name)

    try:
        return v1_core.create_namespaced_pod_binding(pod_name, namespace, body)
    except client.rest.ApiException as e:
        logger.info("Exception when calling create_namespaced_pod_binding: %s\n" % json.loads(e.body)['message'])
    except:
        logger.info("An exception occured!")

    return False

# Listen for tasks in the node's queue
def listen_for_tasks(r):
    while True:
        if r.exists("pending_tasks"):
            task = r.rpop("pending_tasks")
            task_name = task.decode('utf-8')
            logger.info(f"Received task: {task_name}")
            try:
                scheduler(task_name, node_name)
            except Exception as e:
                logger.info(f"Error processing task {task_name}: {e}")
        else:
            time.sleep(5)  # No tasks, wait for a bit before checking again

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
    logger.info("Starting node agent...")
    redis = wait_redis(host=f'{node_name}-redis-service')
    listen_for_tasks(redis)
