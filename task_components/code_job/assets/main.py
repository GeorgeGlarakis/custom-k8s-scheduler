import os
import logging
import redis
from redis.commands.json.path import Path

import code

# Initialize environmental variables
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
node_name = os.environ.get('NODE_NAME')
data_id   = os.environ.get('DATA_ID')
namespace = os.environ.get('NAMESPACE', 'default')

def sort_data(logger):
    try:
        # Connect to Redis instance
        r = redis.StrictRedis(host=f'{node_name}-worker-redis-service.{namespace}.svc.cluster.local', port=6379)
        logger.debug(f"Connected to Redis at {node_name}.{namespace}.svc.cluster.local")

        data = r.json().get(f"data:{data_id}")
        array = data["list"]
        logger.debug(f"Received data: {array}")

        sorted_array = code.main(array)
        logger.debug(f"Sorted data: {sorted_array}")
        r.json().set(f"data:{data_id}", Path.root_path(), {"list": sorted_array})

        logger.info(f"Sorted data saved successfully.")
        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        return e

if __name__ == "__main__":
    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='code_job_logfile.log', encoding='utf-8', level=logging.DEBUG)

    sort_data(logger)