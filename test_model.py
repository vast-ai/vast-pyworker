import os
import nltk
from nltk.corpus import words
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
import sys
import datetime

from tgi_backend import TGIBackend
from ooba_backend import OOBABackend
from sd_auto_backend import SDAUTOBackend

HF_SERVER = '127.0.0.1:5001'
MAX_CONCURRENCY = 100

backend_dict = {"TGI" : TGIBackend, "OOBA" : OOBABackend, "SD_AUTO" : SDAUTOBackend}

def num_tokens_to_num_words(num_tokens):
    return num_tokens // 3 #seems roughly accurate for these generated words

class ModelPerfTest:
    def __init__(self, backend="TGI"):
        nltk.download("words")

        self.word_list = words.words()
        self.backend = backend_dict[backend]( #needs to be called with the model already running
            container_id=os.environ['CONTAINER_ID'],
            master_token=os.environ['MASTER_TOKEN'],
            control_server_url=os.environ['REPORT_ADDR'],
            send_data=False
        )
        self.avg_total_tokens = None
        self.avg_batch_total_tokens = None
        print(f'ModelPerfTest: init complete')

    def update_params(self, max_total_tokens, max_batch_total_tokens):
        self.avg_total_tokens = max_total_tokens // 2
        self.avg_batch_total_tokens = (max_batch_total_tokens * 3) // 4
    
    def make_random_prompt(self, prompt_len):
        return " ".join(random.choices(self.word_list, k=prompt_len))

    def prompt_model(self, num_prompt_tokens, num_output_tokens):
        prompt = self.make_random_prompt(num_tokens_to_num_words(num_prompt_tokens))
        model_request = {"inputs" : prompt, "parameters" : {"max_new_tokens" : num_output_tokens}} #need to add a function to handle this (is different for OOBA)
        rcode, _, time = self.backend.generate(model_request, metrics=False)
        if (rcode != 200):
            print(f"{datetime.datetime.now()} prompt_model returned {rcode}!")
        gentokens = 0
        if (rcode == 200):
            gentokens = num_prompt_tokens + num_output_tokens
        return rcode, time, gentokens

    def send_batch(self, req_total_tokens):
        futures = []
        t1 = time.time()
        with ThreadPoolExecutor(MAX_CONCURRENCY) as e:
            for (num_prompt_tokens, num_output_tokens) in req_total_tokens:
                future = e.submit(self.prompt_model, num_prompt_tokens, num_output_tokens)
                futures.append(future)

        print("sent batch and waiting")
        sys.stdout.flush()
        
        total_latency = 0.0
        num_reqs_completed = 0
        total_gentokens = 0
        for future in futures:
            rcode, latency, gentokens = future.result()
            if (latency is not None) and (rcode == 200):
                total_latency += latency
                total_gentokens += gentokens
                num_reqs_completed += 1

        print("batch returning")
        sys.stdout.flush()
        
        t2 = time.time()
        return t2 - t1, total_latency, total_gentokens, num_reqs_completed
    
    def first_run(self):
        print("starting first run")
        sys.stdout.flush()
        num_reqs = 16
        req_total_tokens = [(48, 16)] * num_reqs # total_tokens = 64
        time_elapsed, total_latency, total_gentokens, num_reqs_completed = self.send_batch(req_total_tokens)
        throughput = total_gentokens / time_elapsed
        avg_latency = total_latency / num_reqs_completed
        print(f"{datetime.datetime.now()} first run completed, time_elapsed: {time_elapsed}, avg_latency: {avg_latency}, throughput: {throughput}, num_reqs_completed: {num_reqs_completed}")
        sys.stdout.flush()

        if (throughput < 50.0) or (num_reqs_completed != num_reqs): #some machines give ~75.0
            return False
        else:
            return True
        
    def run(self, num_batches):
        if num_batches < 1:
            raise ValueError("can't run with less than one perf benchmark iteration!")

        batches = []
        success = True
        for batch_num in range(num_batches):
            batch_total_tokens = int(np.random.normal(loc=self.avg_batch_total_tokens, scale=5.0, size=1))
            num_reqs = batch_total_tokens // self.avg_total_tokens
            req_total_tokens = [(int(3 * (tt // 4)), int(tt // 4)) for tt in np.random.normal(loc=self.avg_total_tokens, scale=5.0, size=num_reqs)]
            print(f"{datetime.datetime.now()} starting test batch: {batch_num} with {num_reqs} concurrent reqs of average total_token num: {self.avg_total_tokens}")
            sys.stdout.flush()
            
            time_elapsed, total_latency, total_gentokens, num_reqs_completed = self.send_batch(req_total_tokens)
            throughput = total_gentokens / time_elapsed
            avg_latency = total_latency / num_reqs_completed if num_reqs_completed != 0 else 0.0

            print(f"{datetime.datetime.now()} batch: {batch_num} took: {time_elapsed} ... throughput: {throughput} (tokens / s), avg_latency: {avg_latency} (seconds), num_reqs: {num_reqs}, num_reqs_completed: {num_reqs_completed}")
            sys.stdout.flush()
            batches.append((throughput, avg_latency, num_reqs, num_reqs_completed))

        throughput, avg_latency, num_reqs, num_reqs_completed =  tuple((sum(series) / num_batches) for series in zip(*batches))
        if num_reqs != num_reqs_completed:
            print(f"{datetime.datetime.now()} only {num_reqs_completed} reqs completed out of {num_reqs} reqs started")
        
        success = ((num_reqs_completed / num_reqs) > 0.75)

        return success, throughput, avg_latency
