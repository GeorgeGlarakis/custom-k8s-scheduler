from kubernetes import client, config, watch
import redis
import time
import os
import logging
import requests
import json
from redis.commands.json.path import Path

import code_job

# Initialize environmental variables
node_name = os.environ.get('NODE_NAME') 
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

def scheduler(task_info):    
    try:
        job_info = {
            'JOB_NAME'   : f'task-{task_info["task_id"]}',
            'IMAGE_NAME' : task_info["image"],
            'IMAGE_TAG'  : task_info["tag"],
            'DATA_ID'    : task_info["data_id"],
            'NODE_NAME'  : task_info["node_name"],
        }

        code_job.main(job_info)


    
        return True
    except Exception as e:
        logger.error(f"Exception when calling create_namespaced_pod_binding: {e}")

    return False

def watch_job_completion(job_name, namespace='default'):
    w = watch.Watch()
    for event in w.stream(v1_batch.list_namespaced_job, namespace=namespace):
        if event['reason'] == "Completed":
            job = event['object']
            if job.metadata.name == job_name and \
                job.status.succeeded and job.status.succeeded >= 1:

                logger.info(f"Job {job_name} completed successfully.")
                break
            elif job.metadata.name == job_name and \
                job.status.failed and job.status.failed > 0:

                logger.error(f"Job {job_name} failed.")
                break

def listen_for_tasks(r, interval=5):
    while True:
        if r.exists("pending_tasks"):
            task = r.rpop("pending_tasks")
            task_name = task.decode('utf-8')
            logger.info(f"Received task: {task_name}")
            try:
                scheduler(task_name, node_name)
                watch_job_completion(task_name)
            except Exception as e:
                logger.error(f"Error processing task {task_name}: {e}")
        else:
            time.sleep(interval)

def send_data(logger,redis, data_id):
    try:
        data = redis.json().get(f"data:{data_id}")
        return data
    
    except Exception as e:
        logger.error(f"Error getting data {data_id}: {e}")
        return e
    
def get_data(logger, redis, node_name, data_id):
    try:
        url = f"http://{node_name}-worker-agent-service.default.svc.cluster.local:8080/api/v1/get_data/{data_id}"
        response = requests.get(url)
        response_body = response.json()

        redis.json().set(f"data:{data_id}", Path.root_path(), response_body["data"])
        return True
    except Exception as e:
        logger.error(f"Error getting data {data_id}: {e}")
        return e
    

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

if __name__ == "__main__":
    # Load Kubernetes configuration
    # config.load_kube_config() ## <-- for debugging, running outside the cluster
    config.load_incluster_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='node_agent_logfile.log', encoding='utf-8', level=log_level)

    # Set up Kubernetes API client
    v1_apps = client.AppsV1Api()
    v1_core = client.CoreV1Api()
    v1_batch = client.BatchV1Api()

    logger.info("Starting node agent...")
    redis = wait_redis(host=f'{node_name}-worker-redis-service')
    listen_for_tasks(redis)
