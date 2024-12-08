from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import datetime
import pickle
import json

import master_code

app = Flask(__name__)
CORS(app)

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

@app.route('/api/v1/task', methods=['POST'])
def create_task():
    body = request.get_json()
    code_id = body['code_id']
    data_id = body['data_id']

    # Trigger evaluation of code, data and node
    node_selection, execution_time = master_code.evaluate_task(code_id, data_id)
    task_info = {
        "task_id": int(hash(datetime.now())),
        "code_id": code_id,
        "data_id": data_id,
        "node_name": node_selection,
        "execution_time": execution_time,
        "status": "pending",
        "time_created": datetime.now(),
        "time_completed": ""
    }
    master_code.set_task(task_info)
    return jsonify("{'status':'scheduled'}", status=201)

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