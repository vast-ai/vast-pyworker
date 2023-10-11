import os
import nltk
from nltk.corpus import words
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import time
import sys

from tgi_backend import TGIBackend

HF_SERVER = '127.0.0.1:5001'
MAX_CONCURRENCY = 100

def num_tokens_to_num_words(num_tokens):
    return num_tokens // 3 #seems roughly accurate for these generated words

class ModelPerfTest:
    def __init__(self, max_total_tokens, max_batch_total_tokens):
        nltk.download("words")
        self.max_total_tokens = max_total_tokens
        self.avg_total_tokens = max_total_tokens // 2
        self.max_batch_total_tokens = max_batch_total_tokens
        self.avg_batch_total_tokens = (max_batch_total_tokens * 3) // 4

        self.word_list = words.words()
        #needs to be called with the model already running, at least for now
        self.backend = TGIBackend(container_id=os.environ['CONTAINER_ID'],
                                  master_token=os.environ['MASTER_TOKEN'],
                                  control_server_url=os.environ['REPORT_ADDR'],
                                  tgi_server_addr=HF_SERVER,
                                  send_data=False)

        self.data = [] # data[i] = (prompt_tokens, output_tokens, output_time)

    def make_random_prompt(self, prompt_len):
        return " ".join(random.choices(self.word_list, k=prompt_len))

    def prompt_model(self, num_prompt_tokens, num_output_tokens):
        prompt = self.make_random_prompt(num_tokens_to_num_words(num_prompt_tokens))
        parameters = {"max_new_tokens" : num_output_tokens}
        rcode, _, time = self.backend.generate(inputs=prompt, parameters=parameters)
        if (rcode != 200):
            print(f"{datetime.datetime.now()} prompt_model returned {rcode}!")
        gentokens = 0
        if (rcode == 200):
            gentokens = num_prompt_tokens + num_output_tokens
        return rcode,time, gentokens

    def run(self, num_batches):
        # not 100% guaranteed that all these reqs will be completed in one model batch
        if num_batches < 1:
            raise ValueError("can't run with less than one perf benchmark iteration!")

        batches = []
        for batch_num in range(num_batches):
            batch_total_tokens = int(np.random.normal(loc=self.avg_batch_total_tokens, scale=5.0, size=1))
            num_reqs = batch_total_tokens // self.avg_total_tokens
            req_total_tokens = [(int(3 * (tt // 4)), int(tt // 4)) for tt in np.random.normal(loc=self.avg_total_tokens, scale=5.0, size=num_reqs)]
            print(f"{datetime.datetime.now()} starting test batch: {batch_num} with {num_reqs} concurrent reqs of average total_token num: {self.avg_total_tokens}")
            sys.stdout.flush()
            futures = []
            t1 = time.time()
            with ThreadPoolExecutor(MAX_CONCURRENCY) as e:
                for (num_prompt_tokens, num_output_tokens) in req_total_tokens:
                    future = e.submit(self.prompt_model, num_prompt_tokens, num_output_tokens)
                    futures.append(future)

            total_latency = 0.0
            num_reqs_completed = 0
            total_gentokens = 0
            for future in futures:
                rcode, latency, gentokens = future.result()
                if (latency is not None) and (rcode == 200):
                    total_latency += latency
                    total_gentokens += gentokens
                    num_reqs_completed += 1

            # all reqs have finished by this point
            t2 = time.time()
            throughput = total_gentokens / (t2 - t1)

            avg_latency = total_latency / num_reqs_completed if num_reqs_completed != 0 else 0.0
            print(f"{datetime.datetime.now()} batch: {batch_num} took: {t2 - t1} ... throughput: {throughput} (tokens / s), avg_latency: {avg_latency} (seconds), num_reqs: {num_reqs}, num_reqs_completed: {num_reqs_completed}")
            sys.stdout.flush()
            batches.append((throughput, avg_latency, num_reqs, num_reqs_completed))

        throughput, avg_latency, num_reqs, num_reqs_completed =  tuple((sum(series) / num_batches) for series in zip(*batches))
        if num_reqs != num_reqs_completed:
            print(f"{datetime.datetime.now()} only {num_reqs_completed} reqs completed out of {num_reqs} reqs started")

        return throughput, avg_latency
