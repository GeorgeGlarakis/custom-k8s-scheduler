from kubernetes import client, config
import redis
import time
import json
import os
import logging

# Load Kubernetes configuration
config.load_kube_config() ## <-- for debugging, running outside the cluster
# config.load_incluster_config()

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)

# Set up Kubernetes API client
v1_apps = client.AppsV1Api()
v1_core = client.CoreV1Api()
v1_batch = client.BatchV1Api()

# Initialize environmental variables
node_name = "node-m02"

def replace_job(job, namespace):
    env_var = client.V1EnvVar(name='NODE_NAME', value=node_name)

    # body = client.V1Job(spec=job.spec, metadata=job.metadata)
    job.spec.template.spec.containers[0].env = [env_var]

    logger.debug(v1_batch.replace_namespaced_job(name=job.metadata.name, namespace=namespace, body=job))

def get_job(job_name, namespace):
    return v1_batch.read_namespaced_job(job_name, namespace)

if __name__ == "__main__":
    job = get_job("code-job", "default")
    replace_job(job, "default")