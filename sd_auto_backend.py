import time
import requests
from img_model_backend import IMGBackend

MODEL_SERVER = '127.0.0.1:5001'

class SDAUTOBackend(IMGBackend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        super().__init__(container_id, control_server_url, master_token, send_data)
        self.model_server_addr = MODEL_SERVER

    def generate(self, model_request):
        self.metrics.start_req(model_request)
        try:
            t1 = time.time()
            response = requests.post(f"http://{self.model_server_addr}/sdapi/v1/txt2img", json=model_request)
            t2 = time.time()
            self.metrics.finish_req(model_request)

            if response.status_code == 200:
                return 200, response.text, t2 - t1

            return response.status_code, None, None

        except requests.exceptions.RequestException as e:
            print(f"[TGI-backend] Request error: {e}")

        return 500, None, None

    def generate_stream(self, model_request):
        pass