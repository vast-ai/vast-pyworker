from backend import GenericBackend
from tgi.metrics import Metrics as TGIMetrics

import os
import time
from threading import Thread, Event
from vllm import EngineArgs, SamplingParams
from vastvllm.vllm_engine import VLLMEngine
from flask import abort

TIMEOUT = 100

class Backend(GenericBackend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        #will need to update metrics for compatibility
        metrics = TGIMetrics(id=container_id, master_token=master_token, control_server_url=control_server_url, send_server_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        engine_args = EngineArgs(model=os.environ["MODEL_NAME"])
        self.engine = VLLMEngine(engine_args=engine_args)
        engine_thread = Thread(target=self.engine.run)
        engine_thread.start()

    def generate(self, model_request, metrics=True):
        if metrics:
            self.metrics.start_req(model_request)
        if "inputs" not in model_request.keys() or "parameters" not in model_request.keys(): #will want more sophisticated error checking
            return 400, None

        prompt = model_request["inputs"]
        parameters = model_request["parameters"]
        if "max_new_tokens" in parameters.keys():
            max_new_tokens = parameters["max_new_tokens"]
        else:
            max_new_tokens = 250
        params = SamplingParams(temperature=0.8, top_p=0.95, frequency_penalty=0.1, max_tokens=max_new_tokens)
        event = Event()
        ret_list = []
        t1 = time.time()
        self.engine.prompt_queue.put((prompt, params, event, ret_list))
        event.wait(timeout=TIMEOUT)
        if event.is_set():
            t2 = time.time()
            if self.metrics:
                model_request["time_elapsed"] = t2 - t1
                self.metrics.finish_req(model_request)

            out = ret_list.pop().pop()
            return 200, {"response" : out.text}
        else:
            if metrics:
                self.metrics.error_req(model_request)
            return 500, None

def generate_handler(backend, request):

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)
    else:
        print("WARNING: support for /generate requests without a signed signature will soon be deprecated")

    if model_dict is None:
        print(f"client request: {request.json} doesn't include model inputs and parameters")
        abort(400)

    code, content = backend.generate(model_dict)

    if code == 200:
        return content
    else:
        print(f"generate failed with code {code}")
        abort(code)

flask_dict = {
    "POST" : {
        "generate" : generate_handler
    }
}

