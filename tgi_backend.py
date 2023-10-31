import requests
from flask import Response, request, abort

from server_metrics import TGIServerMetrics
from generic_backend import Backend

MODEL_SERVER = '127.0.0.1:5001'

class TGIBackend(Backend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = TGIServerMetrics(id=container_id, control_server_url=control_server_url, send_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.model_server_addr = MODEL_SERVER

    def generate(self, model_request):
        return super().generate(model_request, self.model_server_addr, "generate", lambda r: r.text, metrics=True)

    def hf_tgi_wrapper(self, inputs, parameters):
        hf_prompt = {"inputs" : inputs, "parameters" : parameters}
        self.metrics.start_req(text_prompt=inputs, parameters=parameters)
        try:
            response = requests.post(f"http://{self.model_server_addr}/generate_stream", json=hf_prompt, stream=True)
            if response.status_code == 200:
                for byte_payload in response.iter_lines():
                    yield byte_payload
                    yield "\n"
            self.metrics.finish_req(text_prompt=inputs, parameters=parameters)
        
        except requests.exceptions.RequestException as e:
            print(f"[TGI-backend] Request error: {e}")

    def generate_stream(self, model_request):
        return Response(self.hf_tgi_wrapper(model_request["inputs"], model_request["parameters"]))

    def health_handler(self):
        return super().generate(None, self.model_server_addr, "health")

    def info_handler(self):
        return super().generate(None, self.model_server_addr, "info")

    def metrics_handler(self):
        return super().generate(None, self.model_server_addr, "metrics")
    
######################################### FLASK HANDLER METHODS ###############################################################

# Can move these functions into the TGIBackend class I think

def generate_handler(backend, request):

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)

    if model_dict is None:
        print(f"client request: {request.json} doesn't include model inputs and parameters")
        abort(400)

    code, content, _ = backend.generate(model_dict)

    if code == 200:
        return content
    else:
        print(f"generate failed with code {code}")
        abort(code)
    
def generate_stream_handler(backend, request):

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)
 
    if model_dict is None:
        print(f"client request: {request.json} doesn't include model inputs and parameters")
        abort(400)

    return backend.generate_stream(model_dict)

def health_handler(backend, request):

    code, content = backend.health_handler()

    if code == 200:
        return content
    else:
        print(f"health failed with code {code}")
        abort(code)

def info_handler(backend, request):

    code, content = backend.info_handler()

    if code == 200:
        return content
    else:
        print(f"info failed with code {code}")
        abort(code)

def metrics_handler(backend, request):

    code, content = backend.metrics_handler()

    if code == 200:
        return content
    else:
        print(f"metrics failed with code {code}")
        abort(code)

flask_dict = {
    "generate" : generate_handler,
    "generate_stream" : generate_stream_handler,
    "health" : health_handler,
    "info" : info_handler,
    "metrics" : metrics_handler
}
