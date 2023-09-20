from flask import Flask, request, abort
import os
import logging

from tgi_backend import TGIBackend

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.DEBUG)

HF_SERVER = '127.0.0.1:5001'

master_token = os.environ['MASTER_TOKEN']
container_id = os.environ['CONTAINER_ID']
control_server_url = os.environ['REPORT_ADDR']

backend = TGIBackend(container_id=container_id, master_token=master_token, control_server_url=control_server_url, tgi_server_addr=HF_SERVER)

@app.route('/tokens', methods=['GET'])
def get_tokens():
    global backend
    if not backend.check_master_token(request.json['mtoken']):
        abort(401)

    return {"tokens" : backend.get_auth_tokens()}

@app.route('/generate', methods=['POST'])
def generate():
    global backend
    if not backend.check_auth_token(request.json['token']):
        abort(401)
    
    code, content = backend.generate(request.json['inputs'], request.json["parameters"])
    if code == 200:
        return content
    else:
        abort(code)

@app.route('/generate_stream', methods=['POST'])
def generate_stream():
    global backend
    if not backend.check_auth_token(request.json['token']):
        abort(401)

    return backend.generate_streaming(request.json['inputs'], request.json["parameters"])
    
@app.route('/report_capacity', methods=['POST'])
def report_capacity():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.report_batch_capacity(request.json)
    return "Reported capacity"

@app.route('/report_done', methods=['POST'])
def report_done():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.finish_req(request.json)
    return "Updated Metrics"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, threaded=True)