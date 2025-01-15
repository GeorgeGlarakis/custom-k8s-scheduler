from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import datetime
import json
import logging
import requests

import node_code

# Initialize environmental variables
this_node = os.environ.get('NODE_NAME') 
log_level = os.environ.get('LOG_LEVEL', 'DEBUG').upper()

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='node_agent_logfile.log', encoding='utf-8', level=log_level)

app = Flask(__name__)
CORS(app)

################################################################################

@app.route('/', methods=['POST', 'GET'])
def index():
    return jsonify({'status':'ok'})

################################################################################

# Master calls this as destination node in Data migration
@app.route('/api/v1/migrate_data', methods=['POST'])
def migrate_data():
    body = request.get_json()
    node_name = body['node_name']
    data_id = body['data_id']

    result = node_code.get_data(logger, this_node, node_name, data_id)
    if result:
        return jsonify({'status':'success'}), 200
    else:
        return jsonify({'error':'failed'}), 400

################################################################################

# Dest-Node calls this as source node in Data migration
@app.route('/api/v1/get_data/<data_id>', methods=['GET'])
def get_data(data_id):

    data = node_code.send_data(logger, this_node, data_id)

    send_data = {
        "timestamp": str(datetime.datetime.now()),
        "data_id": data_id,
        "data": data
    }
    logger.debug(f"Sending: {send_data}")

    return jsonify(send_data), 201

################################################################################

# body = {
#     "source_send": "",
#     "destination_receive": "",
#     "destination_send": "",
#     "source_receive": ""
# }

@app.route('/api/v1/latency/<node_name>', methods=['GET'])
def node_latency(node_name):
    url = f"http://{node_name}-worker-agent-service.default.svc.cluster.local:8080/api/v1/latency/request"

    body = {
        "source_send": "",
        "destination_receive": "",
        "destination_send": "",
        "source_receive": ""
    }
    source_send = datetime.datetime.now()
    body["source_send"] = source_send.timestamp() * 1000
    response = requests.get(url, json=body)
    response_body = response.json()

    source_receive = datetime.datetime.now()
    response_body["source_receive"] = source_receive.timestamp() * 1000

    d1 = response_body["destination_receive"] - response_body["source_send"]
    d2 = response_body["source_receive"] - response_body["destination_send"]
    latency = (d1 + d2)/2

    return jsonify({'latency': latency})

@app.route('/api/v1/latency/request', methods=['GET'])
def latency_request():
    body = request.get_json()
    destination_receive = datetime.datetime.now()
    body["destination_receive"] = destination_receive.timestamp() * 1000

    time.sleep(3)

    destination_send = datetime.datetime.now()
    body["destination_send"] = destination_send.timestamp() * 1000
    return jsonify(body)

################################################################################

if __name__ == '__main__':
    logger.info("Starting node agent...")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
