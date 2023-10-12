from flask import Flask, request, abort
import os
import logging

from tgi_backend import TGIBackend

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

HF_SERVER = '127.0.0.1:5001' #could make this an environment variable in the future

print(f"tgi_server.py")

master_token = os.environ['MASTER_TOKEN']
container_id = os.environ['CONTAINER_ID']
control_server_url = os.environ['REPORT_ADDR']

backend = TGIBackend(container_id=container_id, master_token=master_token, control_server_url=control_server_url, tgi_server_addr=HF_SERVER, send_data=True)

#################################################### CLIENT FACING ENDPOINTS ###########################################################################

@app.route('/generate', methods=['POST'])
def generate():
    global backend

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)

    if model_dict is None:
        print(f"client request: {request.json} doesn't include model inputs and parameters")
        abort(400)

    code, content, _ = backend.generate(**model_dict)

    if code == 200:
        return content
    else:
        print(f"generate failed with code {code}")
        abort(code)

@app.route('/generate_stream', methods=['POST'])
def generate_stream():
    global backend

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)
 
    if model_dict is None:
        print(f"client request: {request.json} doesn't include model inputs and parameters")
        abort(400)

    return backend.generate_stream(**model_dict)

@app.route('/health', methods=['GET'])
def health():
    global backend

    code, content = backend.health_handler()

    if code == 200:
        return content
    else:
        print(f"health failed with code {code}")
        abort(code)

@app.route('/info', methods=['GET'])
def info():
    global backend

    code, content = backend.info_handler()

    if code == 200:
        return content
    else:
        print(f"info failed with code {code}")
        abort(code)

@app.route('/metrics', methods=['GET'])
def metrics():
    global backend

    code, content = backend.metrics_handler()

    if code == 200:
        return content
    else:
        print(f"metrics failed with code {code}")
        abort(code)


#################################################### INTERNAL ENDPOINTS CALLED BY LOGWATCH #################################################################################################
@app.route('/report_capacity', methods=['POST'])
def report_capacity():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.report_batch_capacity(request.json)
    return "Reported capacity"

@app.route('/report_loaded', methods=['POST'])
def report_loaded():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.report_loaded(request.json)
    return "Reported loaded"

@app.route('/report_done', methods=['POST'])
def report_done():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.report_req_stats(request.json)
    return "Updated Metrics"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['AUTH_PORT'], threaded=True)
