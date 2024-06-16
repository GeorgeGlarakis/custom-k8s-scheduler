import sys
from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()
response= v1.list_node()

# for node in response.items:
#     print("\nKubernetes Node Name is " + str(node.metadata.labels['kubernetes.io/hostname']))
#     print(" => Kubernetes Node Image is " + str(node.status.node_info.os_image))
#     for j in node.status.addresses:
#         print(" =>This Node is using address type " + str(j.type) + " for " + str(j.address))  

print(v1.list_namespaced_service('default', field_selector = 'metadata.name=sorting'))
print(v1.list_namespaced_service('default'))