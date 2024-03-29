from kubernetes.client import models
from kubernetes.client import api_client
from kubernetes.client import Configuration
from kubernetes.client import CoreV1Api
from kubernetes.client import V1Pod
from kubernetes import config
import time
# from kubernetes.client import models
# from kubernetes.client import api_client
# from kubernetes.client import Configuration
# from kubernetes.client import CoreV1Api
# from kubernetes.client import V1Pod
from kubernetes import client, config
import time, sys

class CustomScheduler:
    def __init__(self):
        # Set up Kubernetes API client
        # config = Configuration()
        # config.host = "localhost"
        # config.verify_ssl = False  # Adjust based on your security settings

        try:
            config.load_kube_config()
        except FileNotFoundError as e:
            print("Warning %s\n" % e)

        # api_client.Configuration.set_default(config)

        self.api = CoreV1Api()
        self.api = client.CoreV1Api()



    def get_pending_pods(self):
        # Retrieve pending pods from the Kubernetes API
        pod_list = self.api.list_pod_for_all_namespaces(field_selector="status.phase=Pending")
        return pod_list.items

    def schedule(self):
        while True:
            pending_pods = self.get_pending_pods()

            for pod in pending_pods:
                node_name = self.find_available_node()
                if node_name:
                    self.assign_pod_to_node(pod, node_name)

            time.sleep(5)  # Adjust the sleep duration based on your needs

    def find_available_node(self):
        # Retrieve information about all nodes in the cluster
        nodes = self.api.list_node().items

        # Placeholder logic - Find the first node with available resources
        for node in nodes:
            if self.node_has_available_resources(node):
                return node.metadata.name

        return None  # Return None if no available node is found

    def node_has_available_resources(self, node):
        # Placeholder logic - Check if the node has available resources
        # You may need to adjust this based on your resource requirements
        # For simplicity, we assume the node is available if it has no pods scheduled
        return not node.status.capacity.get("cpu", 0) or not node.status.capacity.get("memory", 0)

    def assign_pod_to_node(self, pod, node_name):
        # Assign the pod to the specified node
        pod.spec.node_name = node_name
        self.api.patch_namespaced_pod(name=pod.metadata.name, namespace=pod.metadata.namespace, body=pod)

    def node_info(self):
        response = self.api.list_node()

        for node in response.items:
            print("\nKubernetes Node Name is " + str(node.metadata.labels['kubernetes.io/hostname']))
            print(" => Kubernetes Node Image is " + str(node.status.node_info.os_image))
            for j in node.status.addresses:
                print(" =>This Node is using address type " + str(j.type) + " for " + str(j.address))  

if __name__ == "__main__":
    scheduler = CustomScheduler()
    scheduler.node_info()

