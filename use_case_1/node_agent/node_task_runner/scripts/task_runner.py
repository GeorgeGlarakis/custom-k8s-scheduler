from kubernetes import client, config, watch
import redis
import time
import os
import logging
from redis.commands.json.path import Path
import subprocess
import psycopg2
from datetime import datetime

# Initialize environmental variables
node_name = os.environ.get('NODE_NAME') 
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()

def scheduler(logger, task_info):    
    try:
        job_info = {
            'JOB_NAME'   : f'task-{task_info["task_id"]}',
            'IMAGE_NAME' : task_info["image"],
            'IMAGE_TAG'  : task_info["tag"],
            'DATA_ID'    : task_info["data_id"],
            'TASK_ID'    : task_info["task_id"],
            'NODE_NAME'  : task_info["node_name"],
            'NODE_CPU'   : task_info["node_cpu"]
        }

        subprocess.run(["python3", "code_job.py", 
                        "--job_name", job_info['JOB_NAME'], 
                        "--image_name", job_info['IMAGE_NAME'], 
                        "--image_tag", job_info['IMAGE_TAG'], 
                        "--data_id", str(job_info['DATA_ID']),
                        "--task_id", str(job_info['TASK_ID']),
                        "--node_name", job_info['NODE_NAME'],
                        "--node_cpu", str(job_info['NODE_CPU'])
                    ])

        task_info["status"] = "running"
        redis.json().set(f"task:{task_info['task_id']}", Path.root_path(), task_info)
    
        return job_info['JOB_NAME']
    except Exception as e:
        logger.error(f"Error when creating job: {e}")

    return False

def watch_job_completion(logger, task_id, namespace='default'):
    try:
        job_name = f'task-{task_id}'
        w = watch.Watch()
        for obj in w.stream(v1_batch.list_namespaced_job, namespace=namespace):
            job = obj['object']
            if job.metadata.name == job_name:
                if job.status.succeeded and job.status.succeeded >= 1:
                    task_info = redis.json().get(f"task:{task_id}")
                    task_info["status"] = "completed"
                    redis.json().set(f"task:{task_id}", Path.root_path(), task_info)

                    operation_counts = task_info["operation_counts"]["total_operations"]
                    logger.debug(f"[task-{task_id}] Operation Counts: {operation_counts}")

                    conn = get_conn(logger)
                    cur = conn.cursor()
                    cur.execute(f"""UPDATE task 
                                    SET time_started = '{task_info["time_started"]}',
                                        time_completed = '{task_info["time_completed"]}'
                                        WHERE id = {task_id};
                                """)
                    cur.execute(f"UPDATE node SET used_cpu_cycles = used_cpu_cycles + {int(operation_counts/1000)} WHERE name = '{task_info['node_name']}';")
                    logger.debug(f"[task-{task_id}] update db")
                    conn.commit()
                    cur.close()

                    logger.info(f"Job {job_name} completed successfully.")
                    break
                elif job.status.failed and job.status.failed > 0:
                    task_info = redis.json().get(f"task:{task_id}")
                    task_info["status"] = "failed"
                    redis.json().set(f"task:{task_id}", Path.root_path(), task_info)
                    logger.error(f"Job {job_name} failed.")
                    break

    except Exception as e:
        logger.error(f"Error watching job: {e}")
        return e

def listen_for_tasks(logger, r, interval=5):
    while True:
        if r.exists("pending_tasks"):
            task = r.rpop("pending_tasks")
            task_name = task.decode('utf-8')
            logger.info(f"Received task: {task_name}")
            try:
                task_info = r.json().get(f"task:{task_name}")

                logger.debug(f"Task info: {task_info}")
                
                scheduler(logger, task_info)
                watch_job_completion(logger, task_info["task_id"])
                delete_job(v1_batch, f'task-{task_info["task_id"]}', logger)
            except Exception as e:
                logger.error(f"Error processing task {task_name}: {e}")
        else:
            time.sleep(interval)

def delete_job(v1_batch, job_name, logger):
    try:
        api_response = v1_batch.delete_namespaced_job(
            name = job_name,
            namespace = 'default',
            body = client.V1DeleteOptions(
                propagation_policy = 'Foreground',
                grace_period_seconds = 0))
        logger.info("Job deleted. status='%s'" % str(api_response.status))
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise e

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

def get_conn(logger):
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(
            host =     os.environ.get('POSTGRES_HOST', 'postgres.default.svc.cluster.local'),
            port =     os.environ.get('POSTGRES_PORT', 5432),
            database = os.environ.get('POSTGRES_DB', 'master_db'),
            user =     os.environ.get('POSTGRES_USER', 'master_agent'),
            password = os.environ.get('POSTGRES_PASSWORD', 'master_password')
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        return e

if __name__ == "__main__":
    # Load Kubernetes configuration
    # config.load_kube_config() ## <-- for debugging, running outside the cluster
    config.load_incluster_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='node_task_runner_logfile.log', encoding='utf-8', level=log_level)

    # Set up Kubernetes API client
    v1_apps = client.AppsV1Api()
    v1_core = client.CoreV1Api()
    v1_batch = client.BatchV1Api()
    v1_events = client.EventsV1Api()

    logger.info("Starting node agent...")
    redis = wait_redis(logger, host=f'{node_name}-worker-redis-service')
    listen_for_tasks(logger, redis)