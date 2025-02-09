from kubernetes import client, config, watch
config.load_incluster_config()

def get_node_images(v1_core, node_name):

    node = v1_core.list_node(field_selector=f"metadata.name={node_name}")

    images = node.status.images
    images_list = []
    for image in images:
        if len(image['names'])<2:
            continue
        full_image = image.names[1].rsplit(":",1)
        size = image.sizeBytes
        next_image = {
            'name' : full_image[0],
            'tag' : full_image[1],
            'size_mb' : "{0:.1f}".format(size/1000000.)
        }
        images_list.append(next_image)
    return images_list

v1_core = client.CoreV1Api()
get_node_images(v1_core, "icelab")

################################################################################
import requests
import redis
import psycopg2
node_from = "icelab"
node_to = "typhon"
offset = 100
url = f"http://{node_to}-worker-agent-service.default.svc.cluster.local:8080/api/v1/migrate_data"
r = redis.Redis(host=f'{node_from}-worker-redis-service.default.svc.cluster.local', port=6379)

conn = psycopg2.connect(
    host =     'postgres.default.svc.cluster.local',
    port =     5432,
    database = 'master_db',
    user =     'master_agent',
    password = 'master_password'
)
cur = conn.cursor()

data_list = [2, 4, 6, 8, 10]
for data_id in data_list:
    body = {
       "node_name": f"{node_from}",
       "data_id": data_id + offset
    }
    requests.post(url, json=body)
    r.json().delete(f"data:{data_id + offset}")

    # Update postgres database
    cur.execute(f"""UPDATE node_info
                    SET node_id = (SELECT id FROM node WHERE name = '{node_to}')
                    WHERE pod_id = {data_id + offset} AND pod_type = 'data';""")
    conn.commit()

cur.close()

################################################################################
import requests
# url = "http://node-master-agent-service:8080/api/v1/task"
# url = "http://master-master-agent-service:8080/api/v1/task"
url = "http://icelab-master-agent-service:8080/api/v1/task"

task_list = []
task_1 = {
    "code_id": 1,
    "data_id": 9,
    "policy": "earliest"
}
task_list.append(task_1)
task_2 = {
    "code_id": 2,
    "data_id": 6,
    "policy": "earliest"
}
task_list.append(task_2)
task_3 = {
    "code_id": 3,
    "data_id": 3,
    "policy": "earliest"
}
task_list.append(task_3)
task_4 = {
    "code_id": 2,
    "data_id": 7,
    "policy": "earliest"
}
task_list.append(task_4)
task_5 = {
    "code_id": 4,
    "data_id": 4,
    "policy": "earliest"
}
task_list.append(task_5)
task_6 = {
    "code_id": 1,
    "data_id": 2,
    "policy": "earliest"
}
task_list.append(task_6)
task_7 = {
    "code_id": 2,
    "data_id": 10,
    "policy": "earliest"
}
task_list.append(task_7)
task_8 = {
    "code_id": 3,
    "data_id": 8,
    "policy": "earliest"
}
task_list.append(task_8)
task_9 = {
    "code_id": 2,
    "data_id": 5,
    "policy": "earliest"
}
task_list.append(task_9)
task_10 = {
    "code_id": 4,
    "data_id": 1,
    "policy": "earliest"
}
task_list.append(task_10)


for task in task_list:
    body = {
       "code_id": task["code_id"] + 6,
       "data_id": task["data_id"] + 100,
       "policy": task["policy"]
    }
    requests.post(url, json=body)


################################################################################

import requests
from time import sleep
url = "http://icelab-master-agent-service:8080/api/v1/task"

for i in range(0, 20):
    body = {
       "code_id": 2,
       "data_id": 170 - i,
       "policy": "fairness"
    }
    requests.post(url, json=body)
    sleep(30)

body = {
    "code_id": 2,
    "data_id": 150 - 20,
    "policy": "fairness"
}
requests.post(url, json=body)