from flask import Flask, request, abort
import os
import logging
import importlib

backend_lib = importlib.import_module(f"{os.environ['BACKEND']}.backend")
backend_class = getattr(backend_lib, "Backend")
flask_dict = getattr(backend_lib, "flask_dict")

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

print(f"server.py")
print(f"available endpoints: {flask_dict}")

master_token = os.environ['MASTER_TOKEN']
container_id = os.environ['CONTAINER_ID']
control_server_url = os.environ['REPORT_ADDR']

backend = backend_class(container_id=container_id, master_token=master_token, control_server_url=control_server_url, send_data=True)

#################################################### CLIENT FACING ENDPOINTS ###########################################################################

@app.route('/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handler(endpoint):
    global backend
    if (request.method not in flask_dict.keys()) or (endpoint not in flask_dict[request.method].keys()):
        abort(404)
    
    return flask_dict[request.method][endpoint](backend, request)
    
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

@app.route('/report_error', methods=['POST'])
def report_done():
    global backend
    if ("mtoken" not in request.json.keys()) or not backend.check_master_token(request.json['mtoken']):
        abort(401)
    backend.metrics.report_error(request.json)
    return "Updated Metrics"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['AUTH_PORT'], threaded=True)

