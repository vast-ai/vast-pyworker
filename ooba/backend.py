from flask import abort
import json

from backend import GenericBackend
from ooba.metrics import Metrics

BLOCKING_SERVER = '127.0.0.1:5001'
STREAMING_SERVER = '127.0.0.1:5002' 

class Backend(GenericBackend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = Metrics(id=container_id, master_token=master_token, control_server_url=control_server_url, send_server_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.blocking_server_addr = BLOCKING_SERVER
        self.streaming_server_addr = STREAMING_SERVER

    def generate(self, model_request, metrics=True):
        def response_func(response):
            try:
                response_json = response.json()
                return response_json['results'][0]['text']
            except json.decoder.JSONDecodeError:
                print(f"[OOBA-backend] JSONDecodeError for response: {response.content}")
                return None
            
        return super().generate(model_request, self.blocking_server_addr, "api/v1/generate", response_func, metrics=metrics)
    
    # Doesn't work with websockets
    def generate_stream(self, model_request):
        return "501: Not Implemented"
    
######################################### FLASK HANDLER METHODS ###############################################################

def generate_handler(backend, request):
    
    code, content, _ = backend.generate(request.json)
    
    if code == 200:
        return content
    else:
        print(f"generate failed with code {code}")
        abort(code)

flask_dict = {
    "POST" : {
        "api/v1/generate" : generate_handler
    }
}
