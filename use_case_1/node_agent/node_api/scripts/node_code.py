import os
import requests
import time
import redis
from redis.commands.json.path import Path

# Initialize environmental variables
node_name = os.environ.get('NODE_NAME') 
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

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