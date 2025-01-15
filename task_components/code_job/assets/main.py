import os
import logging
import redis
from redis.commands.json.path import Path

import code

class OperationCounter:
    def __init__(self):
        self.comparisons = 0
        self.swaps = 0
        self.operations = 0
    
    def count_comparison(self):
        self.comparisons += 1
        self.operations += 1
    
    def count_swap(self):
        self.swaps += 1
        self.operations += 1

# Initialize environmental variables
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
node_name = os.environ.get('NODE_NAME')
task_id   = os.environ.get('TASK_ID')
data_id   = os.environ.get('DATA_ID')
namespace = os.environ.get('NAMESPACE', 'default')

def sort_data(r, logger, counter):
    try:
        data = r.json().get(f"data:{data_id}")
        array = data["list"]
        logger.debug(f"[task-{task_id}] Received data: {array}")

        sorted_array = code.main(array, counter)
        logger.debug(f"[task-{task_id}] Sorted data: {sorted_array}")

        r.json().set(f"data:{data_id}", Path.root_path(), {"list": sorted_array})
        logger.info(f"[task-{task_id}] Sorted data saved successfully.")
        return True

    except Exception as e:
        logger.error(f"Error: {e}")
        return e

if __name__ == "__main__":
    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='code_job_logfile.log', encoding='utf-8', level=logging.DEBUG)

    # Connect to Redis instance
    r = redis.StrictRedis(host=f'{node_name}-worker-redis-service.{namespace}.svc.cluster.local', port=6379)
    logger.debug(f"[task-{task_id}] Connected to Redis at {node_name}.{namespace}.svc.cluster.local")

    counter = OperationCounter()

    sort_data(r, logger, counter)

    task_info = r.json().get(f"task:{task_id}")
    task_info["operation_counts"] = {
        "comparisons": counter.comparisons,
        "swaps": counter.swaps,
        "total_operations": counter.operations
    }
    r.json().set(f"task:{task_id}", Path.root_path(), task_info)

    logger.info(f"[task-{task_id}] Finished successfully.")