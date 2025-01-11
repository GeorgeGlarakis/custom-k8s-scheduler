import os
import logging
import redis
from redis.commands.json.path import Path
from pypapi import papi_low as papi
from pypapi import events

import code

# Initialize environmental variables
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()
node_name = os.environ.get('NODE_NAME')
task_id   = os.environ.get('TASK_ID')
data_id   = os.environ.get('DATA_ID')
namespace = os.environ.get('NAMESPACE', 'default')

def sort_data(r, logger):
    try:
        data = r.json().get(f"data:{data_id}")
        array = data["list"]
        logger.debug(f"[task-{task_id}] Received data: {array}")

        sorted_array = code.main(array)
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

    papi.library_init()
    evs = papi.create_eventset()
    papi.add_event(evs, events.PAPI_TOT_CYC)
    papi.start(evs)

    sort_data(r, logger)

    result = papi.stop(evs)
    papi.cleanup_eventset(evs)
    papi.destroy_eventset(evs)

    task_info = r.json().get(f"task:{task_id}")
    task_info["cpu_cycles"] = result[0]
    r.json().set(f"task:{task_id}", Path.root_path(), task_info)

    logger.info(f"[task-{task_id}] Finished successfully.")