import time
from queue import Queue
from vllm import LLMEngine

class VLLMEngine:
    def __init__(self, engine_args):
        self.prompt_queue = Queue()
        self.engine = LLMEngine.from_engine_args(engine_args)
        self.wait_map = {}

    def run(self):
        request_id = 0
        while True:
            while not (self.prompt_queue.empty()):
                (prompt, sampling_params, event, ret_list) = self.prompt_queue.get()
                self.wait_map[str(request_id)] = (event, ret_list)
                self.engine.add_request(str(request_id), prompt, sampling_params)
                request_id += 1

            request_outputs = self.engine.step()
            for request_output in request_outputs:
                if request_output.finished:
                    (event, ret_list) = self.wait_map[request_output.request_id]
                    ret_list.append(request_output.outputs)
                    event.set()