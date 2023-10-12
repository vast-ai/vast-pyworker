import sys
import requests
import time
import random
from threading import Thread
import threading
import requests

def post_request(full_path, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(full_path, json=data, timeout=1)
            # print(f"{time.time()} Notification sent. Response: {response.status_code}")
            return response.status_code
        except requests.Timeout:
            print(f"{time.time()} Request timed out")
        except Exception as e:
            print(f"{time.time()} Error: {e}")
        if attempt < max_retries - 1:
            print(f"{time.time()} retrying post request")
            time.sleep(2)
        else:
            return 0

class LLMServerMetrics: #could inherit from a more generic Metrics
    def __init__(self, id, control_server_url, master_token, send_data):
        self.id = int(id)
        self.control_server_url = control_server_url
        self.master_token = master_token #could get rid of this
        
        self.batch_capacity = None
        self.total_prompt_tokens = 0.0
        self.overloaded = False

        self.num_requests_recieved = 0
        self.num_requests_finished = 0
        self.num_requests_working = 0
        self.num_tokens_working = 0
        self.num_tokens_finished = 0.0 # is periodically reset every interval
        self.curr_queue_time = 0.0
        self.curr_tokens_per_second = 0.0 # this is on a request by request basis, and doesn't take into account concurrent requests because of batching

        self.request_ltime = time.time()
        self.elapsed_avg = 1.0
        self.tokens_per_req_avg = 1024.0

        self.cur_perf = 0.0
        self.max_perf = 1.0
        self.cur_capacity_lastreport = 0.1234

        self.model_loaded = False
        self.loadtime = 0.0
        
        self.cur_load = 0.0
        self.fill_data_lut = 0.0
        self.num_tokens_incoming = 0.0

        
        print(f"LLMServerMetrics({id},{control_server_url},{master_token})")

        self.update_interval = 1.0
        if send_data:
            self.t1 = Thread(target=self.send_data_loop)
            self.t1.start()

    def report_batch_capacity(self, json_data):
        # self.batch_capacity = min(json_data["max_batch_prefill_tokens"], json_data["max_batch_tokens"])
        self.batch_capacity = json_data["max_batch_tokens"]
    
    def send_data(self, data, url, path):
        full_path = url + path
        print(f'[server_metrics] sending data to url: {full_path}, data: {data}')
        #response = requests.post(full_path, json = data)
        #print(f"[server_metrics] Notification sent. Response: {response.status_code}")
        thread = threading.Thread(target=post_request, args=(full_path,data))
        thread.start()
        sys.stdout.flush()
    
    def send_data_loop(self):
        while True:
            if ((random.randint(0, 9) == 3) or (self.cur_capacity_lastreport != self.num_tokens_working)) and self.model_loaded:
                # print("[server-metrics] sending data")
                data = {"id" : self.id, "message" : "data update"}
                self.fill_data(data)
                self.send_data(data, self.control_server_url, "/worker_status/")
            time.sleep(self.update_interval)
    
    def fill_data(self, data):
        data["num_requests_working"] = self.num_requests_working
        
        data["cur_capacity"] = self.num_tokens_working
        data["max_capacity"] = self.batch_capacity
        data["cur_perf"]     = self.cur_perf
        self.cur_capacity_lastreport = self.num_tokens_working
        
        data["curr_tokens_per_second"] = self.curr_tokens_per_second
        data["overloaded"] = self.overloaded
        data["num_requests_recieved"] = self.num_requests_recieved

        ntime = time.time()
        elapsed = ntime - self.fill_data_lut
        if (self.fill_data_lut == 0.0):
            elapsed = 1.0
        self.cur_load = self.num_tokens_incoming / elapsed
        data["cur_load"] = self.cur_load
        self.fill_data_lut = ntime
        self.num_tokens_incoming = 0
        
        if self.model_loaded:
            data["loadtime"] = self.loadtime
            data["max_perf"] = self.max_perf

        #data["curr_queue_time"] = self.curr_queue_time

    #calculate "work ratio" in terms of tokens
    def calc_work_ratio(self):
        if self.batch_capacity is not None:
            return self.num_tokens_working / self.batch_capacity
    
    def start_req(self, text_prompt, parameters):
        self.num_requests_recieved += 1
        self.num_requests_working += 1
        
        num_prompt_tokens = len(text_prompt.split()) #estimate, and could switch to faster option if necessary
        num_req_tokens_started = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working += num_req_tokens_started
        self.num_tokens_incoming += num_req_tokens_started
        self.total_prompt_tokens += num_prompt_tokens
        self.cur_perf = self.num_requests_working * self.curr_tokens_per_second 
    
    def finish_req(self, text_prompt, parameters):
        self.num_requests_finished += 1
        self.num_requests_working -= 1

        num_prompt_tokens = len(text_prompt.split())
        num_req_tokens_finished = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working -= num_req_tokens_finished
        self.num_tokens_finished += num_req_tokens_finished
        self.cur_perf = self.num_requests_working * self.curr_tokens_per_second 

        elapsed = time.time() - self.request_ltime
        self.request_ltime = time.time()

        alpha = 0.95       
        self.elapsed_avg        = alpha*self.elapsed_avg + (1-alpha)*elapsed
        self.tokens_per_req_avg = alpha*self.tokens_per_req_avg + (1-alpha)*num_req_tokens_finished
        #self.cur_perf           = self.tokens_per_req_avg / max(self.elapsed_avg, 0.00001)
        #print(f"cur_perf  {self.cur_perf} = {self.tokens_per_req_avg} / {self.elapsed_avg}")

    def report_loaded(self, log_data):
        self.model_loaded = True
        self.overloaded = False
        if "max_perf" in log_data.keys():
            self.max_perf   = log_data["max_perf"]
        if "loadtime" in log_data.keys():
            self.loadtime   = log_data["loadtime"]
    
    def report_req_stats(self, log_data):
        self.curr_queue_time = log_data["queue_time"]

        tokens_per_second = 1 / log_data["time_per_token"]
        real_tokens_generated = int(log_data["inference_time"] * tokens_per_second)

        alpha = pow(0.5, real_tokens_generated / (4*1024))
        self.curr_tokens_per_second = alpha*self.curr_tokens_per_second + (1.0-alpha)*tokens_per_second
      
        # print(f"real_tokens_generated: {real_tokens_generated}   curr_tokens_per_second  {self.curr_tokens_per_second} = {alpha}*{self.curr_tokens_per_second} + {1.0-alpha}*{tokens_per_second}")

        if (log_data["queue_time"] > log_data["inference_time"]):
            self.overloaded = True
        else:
            self.overloaded = False


