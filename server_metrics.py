import sys
import requests
import time
from threading import Thread

class LLMServerMetrics: #could inherit from a more generic Metrics
    def __init__(self, id, control_server_url, master_token):
        self.id = int(id)
        self.control_server_url = control_server_url
        self.master_token = master_token #could get rid of this
        
        self.batch_capacity = None
        self.total_prompt_tokens = 0.0
        self.avg_prompt_tokens = None #needs to be set by a start_req call
        self.overloaded = False

        self.num_requests_recieved = 0
        self.num_requests_finished = 0
        self.num_requests_working = 0
        self.num_tokens_working = 0
        self.num_tokens_finished = 0.0 # is periodically reset every interval
        self.curr_queue_time = 0.0
        self.curr_tokens_per_second = 0.0 # this is on a request by request basis, and doesn't take into account concurrent requests because of batching

        self.update_interval = 10.0
        self.curr_perf = 0.0
        self.avg_perf = 0.0
        self.num_intervals = 0

        self.t1 = Thread(target=self.update_perf_loop)
        self.t1.start()

    def report_batch_capacity(self, json_data):
        # self.batch_capacity = min(json_data["max_batch_prefill_tokens"], json_data["max_batch_tokens"])
        self.batch_capacity = json_data["max_batch_tokens"]
    
    def send_data(self, data, url, path):
        # data["mtoken"] = self.master_token
        full_path = url + path
        print(f'[server_metrics] sending data to url: {full_path}, data: {data}')
        response = requests.post(full_path, json = data)
        print(f"[server_metrics] Notification sent. Response: {response.status_code}")
        sys.stdout.flush()
    
    def update_perf_loop(self): #how often should this be updated?
        while True:
            print("[server-metrics] updating perf")
            self.update_perf()
            time.sleep(self.update_interval)
    
    def update_perf(self): #might need locks for this
        self.curr_perf = self.num_tokens_finished / self.update_interval
        self.avg_perf = 0.75 * self.avg_perf + 0.25 * self.curr_perf
        self.num_tokens_finished = 0

    
    def fill_data(self, data):
        # data["num_requests_recieved"] = self.num_requests_recieved
        # data["num_requests_finished"] = self.num_requests_finished
        data["num_requests_working"] = self.num_requests_working
        
        data["cur_capacity"] = self.num_tokens_working
        data["max_capacity"] = self.batch_capacity
        data["perf_avg"] = self.avg_perf
        data["perf_curr"] = self.curr_perf

        data["curr_tokens_per_second"] = self.curr_tokens_per_second
        data["overloaded"] = self.overloaded

        #data["curr_queue_time"] = self.curr_queue_time

    #calculate "work ratio" in terms of tokens and report this when a new request starts, and when a request finishes
    def calc_work_ratio(self):
        if self.batch_capacity is not None:
            return self.num_tokens_working / self.batch_capacity
    
    def start_req(self, text_prompt, parameters):
        self.num_requests_recieved += 1
        self.num_requests_working += 1

        print(f"prompt: {text_prompt}")
        sys.stdout.flush()
        
        num_prompt_tokens = len(text_prompt.split()) #estimate, and could switch to faster option if necessary
        self.total_prompt_tokens += num_prompt_tokens
        self.avg_prompt_tokens = self.total_prompt_tokens / self.num_requests_recieved
        self.num_tokens_working += (self.avg_prompt_tokens + parameters["max_new_tokens"]) 
        work_ratio = self.calc_work_ratio()

        data = {"id" : self.id, "message" : "started req", "busy_ratio" : work_ratio}
        self.fill_data(data)
        self.send_data(data, self.control_server_url, "/worker_status/")
    
    def finish_req(self, log_data):
        print(log_data)
        self.curr_queue_time = log_data["queue_time"]
        self.num_requests_finished += 1
        self.num_requests_working -= 1

        tokens_per_second = 1 / log_data["time_per_token"]
        self.curr_tokens_per_second = tokens_per_second #could use a moving average system
        tokens_generated = int(log_data["inference_time"] * tokens_per_second)
        tokens_processed = tokens_generated + self.avg_prompt_tokens
       
        print(f"tokens_generated: {tokens_generated}, tokens_processed: {tokens_processed}")
        self.num_tokens_finished += tokens_generated
        self.num_tokens_working -= tokens_processed
        work_ratio = self.calc_work_ratio()

        if (log_data["queue_time"] > log_data["inference_time"]):
            self.overloaded = True
        else:
            self.overloaded = False

        data = {"id" : self.id, "message" : "finished req", "busy_ratio" : work_ratio}
        self.fill_data(data)
        self.send_data(data, self.control_server_url, "/worker_status/")









