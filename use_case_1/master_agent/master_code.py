from kubernetes import client, config, watch
import random
import redis
import os
import logging

# Load Kubernetes configuration
# config.load_kube_config() ## <-- for debugging, running outside the cluster
config.load_incluster_config()

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

# Initialize environmental variables
node_name = os.environ.get('NODE_NAME', "master")
scheduler_name = os.environ.get('SCHEDULER_NAME', "my-scheduler")

# Initialize Redis (or use any other store)
r = redis.Redis(host=f'{node_name}-redis-service', port=6379)

# Set up Kubernetes API client
v1_apps = client.AppsV1Api()
v1_core = client.CoreV1Api()
v1_batch = client.BatchV1Api()

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

    # Assign the deployment to the selected node
    assign_to_node(pod, assigned_node)

def assign_to_node(pod, assigned_node):
    try:
        node_r = redis.Redis(host=f'{assigned_node}-redis-service', port=6379)
        pod_name = pod.metadata.name
        node_r.hset("pending_deployments", pod_name, pod.metadata.name)
        node_r.lpush("pending_tasks", pod_name)
    except Exception as e:
        logger.info(f"Error assigning pod to node {assigned_node}: {e}")

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
           
if __name__ == "__main__":
    logger.info("Starting master agent...")
    watch_deployments()