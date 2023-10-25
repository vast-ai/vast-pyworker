import requests
from flask import Response
import time
import json

from llm_backend import LLMBackend

BLOCKING_SERVER = '127.0.0.1:5001'
STREAMING_SERVER = '127.0.0.1:5002' 

class OOBABackend(LLMBackend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        super().__init__(container_id=container_id, control_server_url=control_server_url, master_token=master_token, send_data=send_data)
        self.blocking_server_addr = BLOCKING_SERVER
        self.streaming_server_addr = STREAMING_SERVER

    def generate(self, model_request):
        self.metrics.start_req(text_prompt=model_request["prompt"], parameters=model_request)
        try:
            t1 = time.time()
            response = requests.post(f"http://{self.blocking_server_addr}/api/v1/generate", json=model_request)
            t2 = time.time()
            self.metrics.finish_req(text_prompt=model_request["prompt"], parameters=model_request)

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    return 200, response_json['results'][0]['text'], t2 - t1
                
                except json.decoder.JSONDecodeError:
                    print(f"[OOBA-backend] JSONDecodeError")
                    return 500, None, None

            return response.status_code, None, None

        except requests.exceptions.RequestException as e:
            print(f"[OOBA-backend] Request error: {e}")

        return 500, None, None
    
    def ooba_wrapper(self, model_request):
        self.metrics.start_req(text_prompt=model_request["prompt"], parameters=model_request)
        try:
            response = requests.post(f"ws://{self.streaming_server_addr}/api/v1/stream", json=model_request, stream=True)
            if response.status_code == 200:
                for byte_payload in response.iter_lines():
                    yield byte_payload
                    yield "\n"
            self.metrics.finish_req(text_prompt=model_request["prompt"], parameters=model_request)
        
        except requests.exceptions.RequestException as e:
            print(f"[TGI-backend] Request error: {e}")

    def generate_stream(self, model_request):
        # return Response(self.ooba_wrapper(model_request))
        return "501: Not Implemented"

    def health_handler():
        return 501, None

    def info_handler():
        return 501, None

    def metrics_handler():
        return 501, None