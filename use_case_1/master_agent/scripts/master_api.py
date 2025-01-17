from kubernetes import client, config, watch
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime
import json
import logging

import master_code

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='master_agent_logfile.log', encoding='utf-8', level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# Load Kubernetes configuration
# config.load_kube_config() ## <-- for debugging, running outside the cluster
config.load_incluster_config()

# Set up Kubernetes API client
v1_apps = client.AppsV1Api()
v1_core = client.CoreV1Api()
v1_batch = client.BatchV1Api()

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host =     os.environ.get('POSTGRES_HOST', 'postgres.default.svc.cluster.local'),
    port =     os.environ.get('POSTGRES_PORT', 5432),
    database = os.environ.get('POSTGRES_DB', 'master_db'),
    user =     os.environ.get('POSTGRES_USER', 'master_agent'),
    password = os.environ.get('POSTGRES_PASSWORD', 'master_password')
)

################################################################################

@app.route('/', methods=['POST'])
def index():
    return jsonify("{'status':'ok'}")

################################################################################

@app.route('/api/v1/node', methods=['GET'])
def get_nodes():
    cur = conn.cursor()
    cur.execute("SELECT * FROM node")
    node = cur.fetchall()
    return jsonify(node)

@app.route('/api/v1/node/<node_name>', methods=['GET'])
def get_node(node_name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM node WHERE name = %s", (node_name,))
    node = cur.fetchone()
    return jsonify(node)

################################################################################

@app.route('/api/v1/code', methods=['GET'])
def get_codes():
    cur = conn.cursor()
    cur.execute("SELECT * FROM code")
    code = cur.fetchall()
    return jsonify(code)

@app.route('/api/v1/code/<code_name>', methods=['GET'])
def get_code(code_name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM code WHERE name = %s", (code_name,))
    code = cur.fetchone()
    return jsonify(code)

################################################################################

@app.route('/api/v1/data', methods=['GET'])
def get_datas():
    cur = conn.cursor()
    cur.execute("SELECT * FROM data")
    data = cur.fetchall()
    return jsonify(data)

@app.route('/api/v1/data/<data_name>', methods=['GET'])
def get_data(data_name):
    cur = conn.cursor()
    cur.execute("SELECT * FROM data WHERE name = %s", (data_name,))
    data = cur.fetchone()
    return jsonify(data)

################################################################################

@app.route('/api/v1/compatible', methods=['GET'])
def get_compatible():
    cur = conn.cursor()
    cur.execute("SELECT * FROM compatible")
    compatible = cur.fetchall()
    return jsonify(compatible)

################################################################################

@app.route('/api/v1/task', methods=['POST', 'GET'])
def create_task():
    body = request.get_json()
    policy = body['policy']
    code_id = body['code_id']
    data_id = body['data_id']

    cur = conn.cursor()
    cur.execute(f"INSERT INTO task (code_id, data_id) VALUES ({code_id}, {data_id}) RETURNING id")
    task_id = cur.fetchone()[0]
    conn.commit()
    cur.close()

    task_info = {
        "task_id": task_id,
        "code_id": code_id,
        "data_id": data_id,
        "policy": policy,
        "node_name": "",
        "image": "",
        "tag": "",
        "execution_time": "",
        "status": "listed",
        "time_created": str(datetime.now()),
        "time_completed": "",
        "cpu_cycles": ""
    }

    schedule_task = master_code.evaluate_task(task_info, conn, v1_core, logger)
    if schedule_task["status"]:
        return jsonify(schedule_task), 201
    elif schedule_task["error"]:
        return jsonify(schedule_task), 400

################################################################################

@app.route('/api/v1/test_pickle', methods=['GET'])
def test_pickle():
    body = request.get_json()
    data_id = body['data_id']

    test = {
        "test": "this is a test",
        "data_id": data_id,
        "data": [1, 2, 3, 4, 5]
    }

    # pickled_data = pickle.dumps(test)
    pickled_data = json.dumps(test)
    return pickled_data

################################################################################

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)