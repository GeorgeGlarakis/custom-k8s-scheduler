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
    
    print("--- NODES ---")
    print(ready_nodes)
    return ready_nodes

def scheduler(name, node, namespace="default"):
    target=client.V1ObjectReference()
    target.kind="Node"
    target.apiVersion="v1"
    target.name=node
    
    meta=client.V1ObjectMeta()
    meta.name=name

    body=client.V1Binding(target=target)    
    # body.target=target
    body.metadata=meta
    
    return v1.create_namespaced_pod_binding(name, namespace, body)

# def scheduler(pod, node, namespace="default"):
#     # Set node to be scheduled
#     body = {
#         "spec": {
#             "nodeName": node
#         }
#     }

#     scheduler_status = v1.patch_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=body)

#     print("--- SCHEDULER STARUS ---")
#     # print(scheduler_status)
#     return scheduler_status
    

def main():
    print("Custom Scheduler Started Successfully")
    w = watch.Watch()
    print("Start Watching...")
    for event in w.stream(v1.list_namespaced_pod, "default"):
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            print("Try scheduling Pod: ", event['object'].metadata.name)
            try:
                res = scheduler(event['object'].metadata.name, random.choice(nodes_available()))
            except client.rest.ApiException as e:
                print(json.loads(e.body)['message'])
                    
if __name__ == '__main__':
    print("Main called!")
    main()
