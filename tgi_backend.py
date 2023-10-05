import requests
from flask import Response
import time

from llm_backend import LLMBackend

class TGIBackend(LLMBackend):
    def __init__(self, container_id, control_server_url, master_token, tgi_server_addr, send_data=False):
        super().__init__(container_id=container_id, control_server_url=control_server_url, master_token=master_token, send_data=send_data)
        self.tgi_server_addr = tgi_server_addr

    def generate(self, inputs, parameters):
        self.metrics.start_req(text_prompt=inputs, parameters=parameters)
        hf_prompt = {"inputs" : inputs, "parameters" : parameters}
        try:
            t1 = time.time()
            response = requests.post(f"http://{self.tgi_server_addr}/generate", json=hf_prompt)
            t2 = time.time()
            self.metrics.finish_req(text_prompt=inputs, parameters=parameters)

            if response.status_code == 200:
                return 200, response.text, t2 - t1

            return response.status_code, None, None

        except requests.exceptions.RequestException as e:
            print(f"[TGI-backend] Request error: {e}")

        return None, None, None

    def hf_tgi_wrapper(self, inputs, parameters):
        hf_prompt = {"inputs" : inputs, "parameters" : parameters}
        self.metrics.start_req(text_prompt=inputs, parameters=parameters)
        response = requests.post(f"http://{self.tgi_server_addr}/generate_stream", json=hf_prompt, stream=True)
        if response.status_code == 200:
            for byte_payload in response.iter_lines():
                yield byte_payload
                yield "\n"
        self.metrics.finish_req(text_prompt=inputs, parameters=parameters)

    def generate_stream(self, inputs, parameters):
        return Response(self.hf_tgi_wrapper(inputs, parameters)) #might want to add check here for connection error with tgi server
