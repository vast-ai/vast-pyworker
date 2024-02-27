import random
import time
from threading import Thread, Lock, Event
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
import resource
import psutil
import os
import sys
import signal

import argparse
import nltk
nltk.download("words")
from nltk.corpus import words

from test_LLM import auth_worker

PROMPT_START = "please generate a response as long as you can about"

MAX_CONCURRENCY = 100
JOIN_TIMEOUT = 5
TOKENS_PER_WORD = 1.33

class SimpleSim: #want to work in terms of autoscaler units, want to keep track of current load (requested tokens / second)
    def __init__(self, args, server_address, endpoint_name, trial_t, request_load, api_key):
        self.word_list = words.words()
        self.args = args

        self.server_address = server_address
        self.endpoint_name = endpoint_name
        self.api_key = api_key
        
        self.trial_t = trial_t #units of minutes
        self.start_t = time.time() #units of seconds
        self.curr_t = self.start_t
        self.last_t = self.start_t
        self.end_t =  self.start_t + trial_t * 60 #units of seconds

        self.request_load = request_load
        # self.tokens_per_prompt = 50
        self.tokens_per_prompt = int(len(PROMPT_START.split()) + TOKENS_PER_WORD)
        self.max_tokens_per_response = 250
        self.max_returned_tokens = self.max_tokens_per_response
        self.tokens_per_request = self.tokens_per_prompt + self.max_tokens_per_response
        self.sleep_interval = max(int(self.tokens_per_request / self.request_load), 1)
        
        self.requests_started = 0
        self.requests_finished = 0
        self.new_requests_finished = 0
        self.requests_failed = 0
        self.new_requests_failed = 0
        self.tokens_requested = 0
        self.new_tokens_requested = 0
        self.tokens_finished = 0
        self.new_tokens_finished = 0

        self.load_metrics = []
        self.perf_metrics = []
        self.success_metrics = []
        self.worker_metric_map = {}

        self.threads = []
        self.proc = psutil.Process(os.getpid())
        self.done = False
        # self.lock = Lock()

    # def make_random_prompt(self, prompt_len):
    #     return " ".join(random.choices(self.word_list, k=prompt_len))
    
    def print_summary(self):
        num_ended = self.requests_finished + self.requests_failed
        success_ratio = self.requests_finished / num_ended if num_ended != 0 else 1.0
        print(f"trial done... time interval: {self.curr_t - self.start_t} avg_load: {sum(self.load_metrics) / len(self.load_metrics)}, avg_perf: {sum(self.perf_metrics) / len(self.perf_metrics)}, avg_tokens_per_request: {self.tokens_finished / self.requests_finished} tokens_generated: {self.tokens_finished} requests_started {self.requests_started} requests_finished: {self.requests_finished} requests_failed: {self.requests_failed} success_ratio: {success_ratio}")

    
    def handle_kill(self, sig, frame):
        print(f"handling sig: {sig}")
        self.print_summary()
        for addr, map in self.worker_metric_map.items():
            print(f"worker: {addr}")
            for k, v in map.items():
                print(f"{k}:{v}")
        self.done = True
        sys.exit(0)

    def make_random_prompt(self):
        return f"{PROMPT_START} {random.choice(self.word_list)}"

    def update_loop(self, num_requests):
        with ThreadPoolExecutor(MAX_CONCURRENCY) as e:
            futures = []
            for i in range(num_requests):
                self.requests_started += 1
                self.tokens_requested += self.tokens_per_request
                self.new_tokens_requested += self.tokens_per_request
                future = e.submit(auth_worker, self.args, self.worker_metric_map, self.server_address, self.api_key, self.make_random_prompt(), self.max_tokens_per_response) #self.make_random_prompt(int(self.tokens_per_prompt / TOKENS_PER_WORD))
                futures.append(future)

            while len(futures) > 0:
                done, pending = wait(futures, timeout=10, return_when=ALL_COMPLETED)
                for done_fut in done:
                    if done_fut.result():
                        self.requests_finished += 1
                        self.new_requests_finished += 1
                        response_token_estimate = int(done_fut.result() * TOKENS_PER_WORD)
                        self.max_returned_tokens = max(self.max_returned_tokens, response_token_estimate)
                        # request_tokens = self.tokens_per_prompt + ((response_token_estimate / self.max_returned_tokens) * self.max_tokens_per_response) #hard to calculate
                        request_tokens = self.tokens_per_prompt + response_token_estimate #hard to calculate
                        self.tokens_finished += request_tokens
                        self.new_tokens_finished += request_tokens
                    else:
                        self.requests_failed += 1
                        self.new_requests_failed += 1

                futures = list(pending)

    def update_metrics(self, delta_t):
        print(f"[update_metrics] ... num fds is: {self.proc.num_fds()}")
        cur_load = self.new_tokens_requested / delta_t
        self.load_metrics.append(cur_load)
        self.new_tokens_requested = 0
        cur_perf = self.new_tokens_finished / delta_t
        self.perf_metrics.append(cur_perf)
        new_requests = self.new_requests_finished + self.new_requests_failed
        cur_success = self.new_requests_finished / new_requests if new_requests != 0 else 1.0
        self.success_metrics.append(cur_success)
        print(f"t: {self.curr_t} delta_t: {delta_t} cur_load: {cur_load} cur_perf: {cur_perf} cur_success_ratio: {cur_success} new_reqs_finished: {self.new_requests_finished} new_tokens_finished: {self.new_tokens_finished} total_reqs_failed: {self.requests_failed}")
        self.new_tokens_finished = 0
        self.new_requests_finished = 0
        self.new_requests_failed = 0

        # delta_load = self.request_load - cur_load
    
    def join_threads(self):
        while len(self.threads) > 0:
            print(f"waiting for {len(self.threads)} threads")
            t = self.threads.pop(0)
            t.join(timeout=JOIN_TIMEOUT)
            if t.is_alive():
                self.threads.append(t)
    
    def run(self):
        print(f"starting sim run: {self.trial_t} minutes ... endpoint: {self.endpoint_name} ... request_load (units of tokens/s): {self.request_load} ... tokens_per_request: {self.tokens_per_request}")
        while self.curr_t < self.end_t and not self.done:
            delta_t = self.curr_t - self.last_t
            if (self.curr_t != self.last_t):
                self.last_t = self.curr_t
                self.update_metrics(delta_t)
            else:
                delta_t = 1 #first round
                self.last_t = self.curr_t
            
            next_tokens = self.request_load * delta_t
            
            num_requests = max(int(next_tokens / self.tokens_per_request), 1)
            print(f"t: {self.curr_t} delta_t: {delta_t} sending {num_requests} requests")
            t = Thread(target=self.update_loop, args=(num_requests,))
            t.start() #might need to join these later on
            self.threads.append(t)
            time.sleep(self.sleep_interval)
            self.curr_t = time.time()

        print("new requests done")
        # extra_time = self.sleep_interval * 10
        # jt = Thread(target=self.join_threads)
        # jt.start()
        
        while not self.done: #jt.is_alive() and
            delta_t = self.curr_t - self.last_t
            self.last_t = self.curr_t
            self.update_metrics(delta_t)
            time.sleep(self.sleep_interval)
            self.curr_t = time.time()
            # jt.join(timeout=0)
                
        self.print_summary()

def main():
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    print(f"[sim] starting, and open file soft limit = {soft_limit}, hard limit= {hard_limit}")
    parser = argparse.ArgumentParser(description="Test inference endpoint")
    parser.add_argument("server_address", help="Main server address")
    parser.add_argument("endpoint_name", type=str, help="The name of the autoscaling group endpoint")
    parser.add_argument("trial_t", type=int, help="Trial length in minutes")
    parser.add_argument("request_load", type=int, help="request load in tokens per second")
    parser.add_argument("api_key", help="API Key")
    parser.add_argument("--generate_stream", action="store_true", help="Whether to generate a streaming request or not")
    parser.add_argument("--backend", help="Name of backend in use on worker server", default="TGI")
    args = parser.parse_args()

    sim = SimpleSim(args, args.server_address, args.endpoint_name, args.trial_t, args.request_load, args.api_key)
    signal.signal(signal.SIGINT, sim.handle_kill)
    sim.run()



if __name__ == "__main__":
    main()





# def update(self, i):
#     t = Thread(target=self.update_loop, args=(i,))
#     self.thread_queue.put((i, t))
#     t.start()


# def join_rest(self):
#     while self.thread_queue.qsize() > 0:
#         i, t = self.thread_queue.get()
#         print(f"joining: {i}")
#         t.join()

# def join_background(self, event):
#     while not event.is_set():
#         while self.thread_queue.qsize() > 0:
#             if event.is_set():
#                 break
#             (i, t) = self.thread_queue.get()
#             t.join(timeout=JOIN_TIMEOUT)
#             if (t.is_alive()):
#                 self.thread_queue.put((i, t))

#         time.sleep(10)

# def run(self):
#     soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)



