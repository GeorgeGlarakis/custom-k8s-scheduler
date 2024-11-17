from kubernetes import client, config
import logging
import argparse

job_name = "migration-job"

def create_job_object(migration_object, logger):
    try:
        # Configureate Pod template container
        container = client.V1Container(
            name='migration-agent',
            image='docker.io/glarakis99/migration_code:latest',
            image_pull_policy='Always',
            env=[
                client.V1EnvVar(
                    name='SOURCE_NODE',
                    value=migration_object["source_node"]),
                client.V1EnvVar(
                    name='DESTINATION_NODE',
                    value=migration_object["destination_node"]),
                client.V1EnvVar(
                    name='NAMESPACE',
                    value_from=client.V1EnvVarSource(
                        field_ref=client.V1ObjectFieldSelector(
                            field_path='metadata.namespace'))),
                client.V1EnvVar(
                    name='DATA_DEPLOYMENT_NAME',
                    value=migration_object["data_deployment_name"]),
                client.V1EnvVar(
                    name='BACKUP_FILE_NAME',
                    value='dump.rdb'),
                client.V1EnvVar(
                    name='PV_PATH',
                    value='/mnt/data'),
                client.V1EnvVar(
                    name='REDIS_PORT',
                    value='6379')
            ],
            volume_mounts=[
                client.V1VolumeMount(
                    name='source',
                    mount_path='/mnt/source',
                    sub_path=f"{migration_object['data_deployment_name']}"),
                client.V1VolumeMount(
                    name='destination',
                    mount_path='/mnt/destination',
                    sub_path=f"{migration_object['data_deployment_name']}")
            ]
        )
        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={'name': job_name}),
            spec=client.V1PodSpec(
                restart_policy='OnFailure', 
                containers=[container],
                volumes=[
                    client.V1Volume(
                        name='source',
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name=f"{migration_object['source_node']}-pvc")),
                    client.V1Volume(
                        name='destination',
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name=f"{migration_object['destination_node']}-pvc"))
                    ]
            )
        )
        # Create the specification of deployment
        spec = client.V1JobSpec(template=template)
        # Instantiate the job object
        job = client.V1Job(
            api_version='batch/v1',
            kind='Job',
            metadata=client.V1ObjectMeta(name=job_name),
            spec=spec
        )
        logger.debug(f"Job object: {job}")
        return job
    except Exception as e:
        logger.error(f"Error creating job object: {e}")
        raise e


def create_job(v1_batch, job, logger):
    try:
        api_response = v1_batch.create_namespaced_job(
            body=job,
            namespace='default')
        logger.info("Job created. status='%s'" % str(api_response.status))
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise e

def delete_job(v1_batch, logger):
    try:
        api_response = v1_batch.delete_namespaced_job(
            name=job_name,
            namespace='default',
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=0))
        logger.info("Job deleted. status='%s'" % str(api_response.status))
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise e

def main(migration_object):
    # config.load_incluster_config()
    config.load_kube_config()

    # Initialize logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='migration_job_logfile.log', encoding='utf-8', level=logging.DEBUG)
    
    v1_batch = client.BatchV1Api()
    
    job = create_job_object(migration_object, logger)

    create_job(v1_batch, job, logger)
    # delete_job(v1_batch, logger)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source_node', dest='source_node', help='Source Node name', required=True)
    parser.add_argument('--destination_node', dest='destination_node', help='Destination Node name', required=True)
    parser.add_argument('--data_deployment_name', dest='data_deployment_name', help='Data Deployment name', required=True)
    args = parser.parse_args()

    migration_object = {
        'source_node': args.source_node,
        'destination_node': args.destination_node,
        'data_deployment_name': args.data_deployment_name
    }
    main(migration_object)

    