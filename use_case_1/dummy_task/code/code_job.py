from kubernetes import client, config
import logging
import argparse

IMAGE_REGISTRY = "docker.io/glarakis99"
LOG_LEVEL = "DEBUG"

def create_job_object(job_info, logger):
    try:
        # Configure Pod template
        container = client.V1Container(
            name = job_info['JOB_NAME'],
            image = f"{IMAGE_REGISTRY}/{ job_info['IMAGE_NAME'] }:{job_info['IMAGE_TAG']}",
            image_pull_policy = 'IfNotPresent',
            env = [
                client.V1EnvVar(
                    name = 'LOG_LEVEL',
                    value = LOG_LEVEL ),
                client.V1EnvVar(
                    name = 'DATA_ID',
                    value = job_info['DATA_ID']),
                client.V1EnvVar(
                    name = 'NAMESPACE',
                    value_from = client.V1EnvVarSource(
                        field_ref = client.V1ObjectFieldSelector(
                            field_path = 'metadata.namespace'
                        )
                    )
                )
            ]
        )
        # Configure nodeAffinity
        affinity = client.V1Affinity(
            node_affinity = client.V1NodeAffinity(
                required_during_scheduling_ignored_during_execution=client.V1NodeSelector(
                    node_selector_terms = [
                        client.V1NodeSelectorTerm(
                            match_expressions = [
                                client.V1NodeSelectorRequirement(
                                    key = 'kubernetes.io/hostname',
                                    operator = 'In',
                                    values = [ job_info['NODE_NAME'] ]
                                )
                            ]
                        )
                    ]
                )
            )
        )

        # Create and configure a spec section
        template = client.V1PodTemplateSpec(
            metadata = client.V1ObjectMeta(labels = {'app': job_info['IMAGE_NAME'], 'type': 'code'}),
            spec = client.V1PodSpec(
                restart_policy = 'OnFailure', 
                containers = [container],
                affinity = affinity
            )
        )
        # Create the specification of deployment
        spec = client.V1JobSpec(template=template)
        # Instantiate the job object
        job = client.V1Job(
            api_version = 'batch/v1',
            kind = 'Job',
            metadata = client.V1ObjectMeta(name = job_info['JOB_NAME'], labels = {'app': job_info['IMAGE_NAME']}),
            spec = spec
        )
        logger.debug(f"Job object: {job}")
        return job
    except Exception as e:
        logger.error(f"Error creating job object: {e}")
        raise e


def create_job(v1_batch, job, logger):
    try:
        api_response = v1_batch.create_namespaced_job(
            body = job,
            namespace = 'default')
        logger.info("Job created. status='%s'" % str(api_response.status))
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise e

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

def main(job_info):
    # config.load_incluster_config()
    config.load_kube_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='code_job_logfile.log', encoding='utf-8', level=logging.DEBUG)
    
    v1_batch = client.BatchV1Api()
    
    job = create_job_object(job_info, logger)

    create_job(v1_batch, job, logger)
    # delete_job(v1_batch, job_info['JOB_NAME'], logger)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--job_name',   dest='job_name',    help='Job Name',    required=True)
    parser.add_argument('--image_name', dest='image_name',  help='Image Name',  required=True)
    parser.add_argument('--image_tag',  dest='image_tag',   help='Image Tag',   required=True)
    parser.add_argument('--data_id',    dest='data_id',     help='Data ID',   required=True)
    parser.add_argument('--node_name',  dest='node_name',   help='Node Name',   required=True)
    args = parser.parse_args()

    job_info = {
        'JOB_NAME'   : args.job_name,
        'IMAGE_NAME' : args.image_name,
        'IMAGE_TAG'  : args.image_tag,
        'DATA_ID'  : args.data_id,
        'NODE_NAME'  : args.node_name,
    }

    main(job_info)

# python3 code_job.py --job_name=code-job --image_name=code_pod --image_tag=latest --data_id=1 --node_name=node-m02