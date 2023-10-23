import requests
import time
import json

from llm_backend import LLMBackend

class OOBABackend(LLMBackend):
    def __init__(self, container_id, control_server_url, master_token, model_server_addr, send_data):
        super().__init__(container_id=container_id, control_server_url=control_server_url, master_token=master_token, send_data=send_data)
        self.model_server_addr = model_server_addr

    def generate(self, model_request):
        self.metrics.start_req(text_prompt=model_request["prompt"], parameters=model_request)
        try:
            t1 = time.time()
            response = requests.post(f"http://{self.tgi_server_addr}/api/v1/generate", json=model_request)
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
    
    def generate_stream(self, model_request):
        pass