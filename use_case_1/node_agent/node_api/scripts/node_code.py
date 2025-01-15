import requests
import time
import redis
from redis.commands.json.path import Path

def send_data(logger, this_node, data_id):
    try:
        redis = wait_redis(logger, host=f'{this_node}-worker-redis-service')
        data = redis.json().get(f"data:{data_id}")
        logger.debug(f"[{this_node}] Data {data_id} retrieved successfully.")
        logger.debug(f"[{this_node}] Data: {data}")
        return data
    
    except Exception as e:
        logger.error(f"Error sending data {data_id}: {e}")
        return e
    
def get_data(logger, this_node, node_name, data_id):
    try:
        url = f"http://{node_name}-worker-agent-service.default.svc.cluster.local:8080/api/v1/get_data/{data_id}"
        response = requests.get(url)
        response_body = response.json()

        logger.debug(f"Data-{data_id}: {response_body}")

        redis = wait_redis(logger, host=f'{this_node}-worker-redis-service')
        redis.json().set(f"data:{data_id}", Path.root_path(), response_body["data"])
        return True
    except Exception as e:
        logger.error(f"Error getting data {data_id}: {e}")
        return False

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