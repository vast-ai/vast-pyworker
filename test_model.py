import os
import nltk
from nltk.corpus import words
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
import sys
import datetime
import importlib
import math
import json

if 'BACKEND' in os.environ:
    backend_lib = importlib.import_module(f"{os.environ['BACKEND']}.backend")
    backend_class = getattr(backend_lib, "Backend")

HF_SERVER = '127.0.0.1:5001'
MAX_CONCURRENCY = 100
TOKENS_PER_WORD = 2.75 #right for these random words

nltk.download("words")
WORD_LIST = words.words()
PROMPT_START = "please generate a response as long as you can about"

def make_random_prompt(input_cost, special=False):
    if special:
        return f"{PROMPT_START} {random.choice(WORD_LIST)}"
    else:
        return " ".join(random.choices(WORD_LIST, k=num_tokens_to_num_words(input_cost)))
    
def format_tgi_payload(worker_payload, prompt_input, output_cost):
    worker_payload["inputs"] = prompt_input
    worker_payload["parameters"] = {"max_new_tokens" : output_cost}

def format_ooba_payload(worker_payload, prompt_input, output_cost):
    worker_payload["prompt"] = prompt_input
    worker_payload["max_new_tokens"] = output_cost

def format_sdauto_payload(worker_payload, prompt_input, output_cost):
    side_length = int(math.sqrt(output_cost))
    make_sdauto_payload(worker_payload, prompt_input, height=side_length, width=side_length)

def make_sdauto_payload(worker_payload, prompt_input, height=512, width=512, batch_size=1, steps=3):
    sdauto_payload = {
        "batch_size": batch_size,
        "cfg_scale": 7,
        "denoising_strength": 0,
        "enable_hr": False,
        "eta": 0,
        "firstphase_height": 0,
        "firstphase_width": 0,
        "height": height,
        "n_iter": 1,
        "negative_prompt": "",
        "prompt": prompt_input,
        "restore_faces": False,
        "s_churn": 0,
        "s_noise": 1,
        "s_tmax": 0,
        "s_tmin": 0,
        "sampler_index": "Euler a",
        "seed": -1,
        "seed_resize_from_h": -1,
        "seed_resize_from_w": -1,
        "steps": steps,
        "styles": [],
        "subseed": -1,
        "subseed_strength": 0,
        "tiling": False,
        "width": width,
    }
    worker_payload.update(sdauto_payload)

payload_dict = {
    "tgi" :   format_tgi_payload,
    "ooba":   format_ooba_payload,
    "sdauto": format_sdauto_payload
}

def num_tokens_to_num_words(num_tokens):
    return int(num_tokens // TOKENS_PER_WORD)

def num_words_to_num_tokens(num_words):
    return int(num_words * TOKENS_PER_WORD)

def get_tgi_output_cost(response):
    resp_json = json.loads(response)
    if "generated_text" in resp_json.keys():
        length = len(resp_json["generated_text"].split())
        # print(f"len: {length}")
        return num_words_to_num_tokens(length)
    else:
        return 0

class ModelPerfTest:
    def __init__(self, backend_name="tgi"):
        self.backend_name = backend_name
        self.backend = backend_class( #needs to be called with the model already running
            container_id=os.environ['CONTAINER_ID'],
            master_token=os.environ['MASTER_TOKEN'],
            control_server_url=os.environ['REPORT_ADDR'],
            send_data=False
        )
        self.avg_req_load = None #load per requests
        self.avg_batch_load = None #load across all requests in a concurrent batch
        print(f'ModelPerfTest: init complete')

    def update_params(self, avg_req_load, max_req_load, avg_batch_load):
        self.avg_req_load = avg_req_load
        self.max_req_load = max_req_load 
        self.avg_batch_load = avg_batch_load #(max_batch_load * 3) // 4
    
    def prompt_model(self, input_cost, output_cost):
        prompt = make_random_prompt(input_cost)
        # print(f"using prompt of cost {input_cost}")
        model_request = {}
        payload_dict[self.backend_name](model_request, prompt, output_cost)

        rcode, response, time = self.backend.generate(model_request, metrics=False)
        # print(f"recieved rcode {rcode}")
        if (rcode != 200):
            print(f"{datetime.datetime.now()} prompt_model with payload: {model_request} returned {rcode}!")
        
        # print(f"returned response: {response} of cost {get_tgi_output_cost(response)}")
        
        genload = 0
        if (rcode == 200):
            if self.backend_name == "tgi":
                genload = input_cost + get_tgi_output_cost(response)
            else:
                genload = input_cost + output_cost

        # print(f"req took time {time}")
        return rcode, time, genload

    def send_batch(self, req_load):
        futures = []
        t1 = time.time()
        with ThreadPoolExecutor(MAX_CONCURRENCY) as e:
            for (input_cost, output_cost) in req_load:
                # if (input_cost + output_cost) > self.max_req_load:
                #     excess_load = input_cost + output_cost - self.max_req_load
                #     input_cost -= math.ceil(excess_load / 2)
                #     output_cost -= math.ceil(excess_load / 2)
                future = e.submit(self.prompt_model, input_cost, output_cost)
                futures.append(future)

        print("sent batch and waiting")
        sys.stdout.flush()
        
        total_latency = 0.0
        num_reqs_completed = 0
        total_genload = 0
        for future in futures:
            rcode, latency, genload = future.result()
            if (latency is not None) and (rcode == 200):
                total_latency += latency
                total_genload += genload
                num_reqs_completed += 1

        print("batch returning")
        sys.stdout.flush()
        
        t2 = time.time()
        return t2 - t1, total_latency, total_genload, num_reqs_completed
    
    def first_run(self):
        print("starting first run")
        sys.stdout.flush()
        num_reqs = 16
        req_load = [(48, 16)] * num_reqs # load = 64
        time_elapsed, total_latency, total_genload, num_reqs_completed = self.send_batch(req_load)
        throughput = total_genload / time_elapsed if time_elapsed != 0 else 0
        avg_latency = total_latency / num_reqs_completed if num_reqs_completed != 0 else float('inf')
        print(f"{datetime.datetime.now()} first run completed, time_elapsed: {time_elapsed}, avg_latency: {avg_latency}, throughput: {throughput}, num_reqs_completed: {num_reqs_completed}")
        sys.stdout.flush()

        if (num_reqs_completed != num_reqs): #some machines give ~75.0 (throughput < 50.0) or 
            return f"throughput: {throughput}<50.0 or ({num_reqs_completed} != {num_reqs})"
        else:
            return "success"
         
    def make_batch_tgi(self, batch_num):
        num_reqs = 56
        input_cost = 800
        output_cost = 256
        req_load = [(input_cost,output_cost) for _ in range(num_reqs)]
        print(f"{datetime.datetime.now()} starting test batch: {batch_num} consisting of {num_reqs} concurrent reqs of input load: {input_cost} output load: {output_cost}")
        sys.stdout.flush()
        return req_load
    
    def make_batch(self, batch_num):
        batch_load = int(np.random.normal(loc=self.avg_batch_load, scale=5.0, size=1))
        num_reqs = batch_load // self.avg_req_load
        req_load = [(int(3 * (tt // 4)), int(tt // 4)) for tt in np.random.normal(loc=self.avg_req_load, scale=5.0, size=num_reqs)]
        print(f"{datetime.datetime.now()} starting test batch: {batch_num} with total_load: {batch_load} consisting of {num_reqs} concurrent reqs of average load: {self.avg_req_load} max load: {self.max_req_load}")
        sys.stdout.flush()
        return req_load
    
    def track_batch(self, req_load, batch_num, batches):
        time_elapsed, total_latency, total_genload, num_reqs_completed = self.send_batch(req_load)
        throughput = total_genload / time_elapsed
        avg_latency = total_latency / num_reqs_completed if num_reqs_completed != 0 else 0.0

        print(f"{datetime.datetime.now()} batch: {batch_num} took: {time_elapsed} ... throughput: {throughput} (load / s), avg_latency: {avg_latency} (seconds), num_reqs: {len(req_load)}, num_reqs_completed: {num_reqs_completed}")
        sys.stdout.flush()
        batches.append((throughput, avg_latency, len(req_load), num_reqs_completed))
    
    def run(self, num_batches):
        if num_batches < 1:
            raise ValueError("can't run with less than one perf benchmark iteration!")
        
        batches = []
        success = True
        for batch_num in range(num_batches):
            req_load = self.make_batch_tgi(batch_num) if self.backend_name == "tgi" else self.make_batch(batch_num)
            self.track_batch(req_load, batch_num, batches)
            
        throughput, avg_latency, num_reqs, num_reqs_completed =  tuple((sum(series) / num_batches) for series in zip(*batches))
        if num_reqs != num_reqs_completed:
            print(f"{datetime.datetime.now()} only {num_reqs_completed} reqs completed out of {num_reqs} reqs started")
        
        success = ((num_reqs_completed / num_reqs) > 0.75)

        return success, throughput, avg_latency
        
