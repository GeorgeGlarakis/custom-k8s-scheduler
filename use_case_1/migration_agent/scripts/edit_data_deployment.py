from kubernetes import client, config
import redis
import time
import os
import logging

# Initialize environmental variables
node_name = os.environ.get('DESTINATION_NODE')
deployment_name = os.environ.get('DATA_DEPLOYMENT_NAME')
namespace = os.environ.get('NAMESPACE')

def replace_deployment(v1_apps, logger, deployment_name, namespace="default"):
    try:
        deployment = v1_apps.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        volumes = deployment.spec.template.spec.volumes
        volumes[0].persistent_volume_claim.claim_name = f"{node_name}-pvc"

        nodeAffinity = deployment.spec.template.spec.affinity.node_affinity
        nodeAffinity.required_during_scheduling_ignored_during_execution.node_selector_terms[0].match_expressions[0].values[0] = node_name

        return v1_apps.replace_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
    except Exception as e:
        logger.error(f"Error editing deployment {deployment_name}: {e}")
        raise e

def wait_redis(host, logger, port=6379, db=0, timeout=60, interval=5):
    start_time = time.time()
    r = redis.Redis(host=host, port=port, db=db)

    while True:
        try:
            # Attempt to ping the Redis server
            if r.ping():
                logger.info("Connected to New Redis!")
                return r
        except redis.exceptions.ConnectionError:
            pass  # Redis server is not yet available

        # Check if the timeout has been exceeded
        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            raise Exception(f"Redis service not available after {timeout} seconds.")

        logger.info(f"Waiting for Redis... ({elapsed_time:.1f}s elapsed)")
        time.sleep(interval)

def main():
    config.load_incluster_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='edit_data_deployment_logfile.log', encoding='utf-8', level=logging.DEBUG)

    v1_apps = client.AppsV1Api()

    replace_deployment(v1_apps, logger, deployment_name, namespace)
    wait_redis(f'{deployment_name}.{namespace}.svc.cluster.local', logger)

    logger.info("Deployment edited successfully.")
    return 1


if __name__ == "__main__":
    main()