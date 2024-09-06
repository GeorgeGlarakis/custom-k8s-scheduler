#!/usr/bin/env python

import time
import random
import json
from datetime import datetime

from kubernetes import client, config, watch

# config.load_kube_config()
config.load_incluster_config()
v1=client.CoreV1Api()

scheduler_name = "my-scheduler"

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                ready_nodes.append(n.metadata.name)
    
    return ready_nodes

def scheduler(name, node, namespace="default"):
    target = client.V1ObjectReference(api_version='v1', kind='Node', name=node, namespace=namespace)

    meta=client.V1ObjectMeta()
    meta.name=name

    body=client.V1Binding(target=target, metadata=meta) # V1Binding is deprecated 

    # body = """{
    #     'api_version': None,
    #     'kind': None,
    #     'metadata': {
    #         'annotations': None,
    #         'creation_timestamp': None,
    #         'deletion_grace_period_seconds': None,
    #         'deletion_timestamp': None,
    #         'finalizers': None,
    #         'generate_name': None,
    #         'generation': None,
    #         'labels': None,
    #         'managed_fields': None,
    #         'name': name,
    #         'namespace': None,
    #         'owner_references': None,
    #         'resource_version': None,
    #         'self_link': None,
    #         'uid': None
    #     },
    #     'target': {
    #         'api_version': 'v1',
    #         'field_path': None,
    #         'kind': 'Node',
    #         'name': node,
    #         'namespace': namespace,
    #         'resource_version': None,
    #         'uid': None
    #     }
    # }"""

    event_response = create_scheduled_event(name, node, namespace, scheduler_name)

    try:
        return v1.create_namespaced_pod_binding(name, namespace, body)
    except client.rest.ApiException as e:
        print("Exception when calling create_namespaced_pod_binding: %s\n" % json.loads(e.body)['message'])
    except:
        print("An exception occured!")

    return False

def create_scheduled_event(name, node, namespace, scheduler_name):
    involved_object = client.V1ObjectReference(kind='Pod', name=name, namespace=namespace)
    involved_object.api_version = "v1"
    involved_object.resource_version = ""
    involved_object.uid = ""

    message = f"Successfully assigned {name} to {node}"

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    metadata = client.V1ObjectMeta()
    metadata.name = name

    event = client.CoreV1Event(involved_object=involved_object, metadata=metadata)
    event.reporting_component = scheduler_name
    event.source  = client.V1EventSource(component=scheduler_name)
    event.message = message
    event.reason  = 'Scheduled'
    event.type    = 'Normal'
    event.count   = 1
    event.first_timestamp = now
    event.last_timestamp  = now
    
    try:
        return v1.create_namespaced_event(namespace, body=event)
    except client.rest.ApiException as e:
        print("Exception when calling create_namespaced_event: %s\n" % json.loads(e.body)['message'])

    return False


# def scheduler(pod, node, namespace="default"):
#     print("Start Scheduling...")
#     body = {
#         "spec": {
#             "nodeName": node
#         }
#     }

#     scheduler_status = v1.patch_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=body)
#     return scheduler_status
    

def main():
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['type'] == "ADDED" and \
           event['object'].spec.scheduler_name == scheduler_name:

            print("Try scheduling Pod: ", event['object'].metadata.name)
            try:
                res = scheduler(event['object'].metadata.name, random.choice(nodes_available()))
            except client.rest.ApiException as e:
                print("Exception when calling scheduler: %s\n" % json.loads(e.body)['message'])
                    
if __name__ == '__main__':
    main()