#!/usr/bin/env python

import time
import random
import json

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
    target=client.V1ObjectReference()
    target.kind="Node"
    target.api_version="v1"
    target.name=node
    target.namespace=namespace

    print(target)
    
    meta=client.V1ObjectMeta()
    meta.name=name

    body=client.V1Binding(target=target)
    body.metadata=meta

    print(body)
    
    return v1.create_namespaced_pod_binding(name, namespace, body)

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
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            print("Try scheduling Pod: ", event['object'].metadata.name)
            try:
                res = scheduler(event['object'].metadata.name, random.choice(nodes_available()))
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])
                    
if __name__ == '__main__':
    main()