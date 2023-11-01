import requests
from flask import Response
import json

from generic_backend import Backend
from server_metrics import OOBAServerMetrics

BLOCKING_SERVER = '127.0.0.1:5001'
STREAMING_SERVER = '127.0.0.1:5002' 

class OOBABackend(Backend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = OOBAServerMetrics(id=container_id, control_server_url=control_server_url, send_server_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.blocking_server_addr = BLOCKING_SERVER
        self.streaming_server_addr = STREAMING_SERVER

    def generate(self, model_request):
        def response_func(response):
            try:
                response_json = response.json()
                return response_json['results'][0]['text']
            except json.decoder.JSONDecodeError:
                print(f"[OOBA-backend] JSONDecodeError")
                return None
            
        return super().generate(model_request, self.blocking_server_addr, "api/v1/generate", response_func, metrics=True)
    
    # Doesn't work with websockets

    # def ooba_wrapper(self, model_request):
    #     self.metrics.start_req(text_prompt=model_request["prompt"], parameters=model_request)
    #     try:
    #         response = requests.post(f"ws://{self.streaming_server_addr}/api/v1/stream", json=model_request, stream=True)
    #         if response.status_code == 200:
    #             for byte_payload in response.iter_lines():
    #                 yield byte_payload
    #                 yield "\n"
    #         self.metrics.finish_req(text_prompt=model_request["prompt"], parameters=model_request)
        
    #     except requests.exceptions.RequestException as e:
    #         print(f"[TGI-backend] Request error: {e}")

    def generate_stream(self, model_request):
        # return Response(self.ooba_wrapper(model_request))
        return "501: Not Implemented"
    
######################################### FLASK HANDLER METHODS ###############################################################

def generate_handler(backend, request):
    return backend.generate(request)

flask_dict = {"api/v1/generate" : generate_handler}
