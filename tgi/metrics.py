import time
import random

from metrics import GenericMetrics

class Metrics(GenericMetrics):
    def __init__(self, id, master_token, control_server_url, send_server_data):
        self.batch_capacity = None
        self.total_prompt_tokens = 0.0
        
        self.num_tokens_working = 0.0
        self.num_tokens_finished = 0.0 # is periodically reset every interval
        
        self.curr_queue_time = 0.0
        self.curr_tokens_per_second = 0.0 # this is on a request by request basis, and doesn't take into account concurrent requests because of batching

        self.request_ltime = time.time()
        self.elapsed_avg = 1.0
        self.tokens_per_req_avg = 1024.0
        self.num_tokens_incoming = 0
        self.num_tokens_errored = 0

        super().__init__(id, master_token, control_server_url, send_server_data)
    
    def send_data_condition(self):
        return ((random.randint(0, 9) == 3) or (self.cur_capacity_lastreport != self.num_tokens_working)) and self.model_loaded
    
    def fill_data(self, data):
        self.fill_data_generic(data)

        data["cur_capacity"] = self.num_tokens_working
        data["max_capacity"] = self.batch_capacity

        self.cur_capacity_lastreport = self.num_tokens_working
        
        data["curr_tokens_per_second"] = self.curr_tokens_per_second
        
        ntime = time.time()
        elapsed = ntime - self.fill_data_lut
        if (self.fill_data_lut == 0.0):
            elapsed = 1.0
        #self.cur_load = (self.num_tokens_incoming + self.num_tokens_errored) / elapsed
        self.cur_load = (self.num_tokens_incoming + self.num_tokens_errored)
        data["cur_load"] = self.cur_load
        self.fill_data_lut = ntime
        self.num_tokens_incoming = 0
        self.num_tokens_errored = 0
        self.num_requests_finished = 0
        
    def _start_req(self, text_prompt, parameters):
        self.num_requests_recieved += 1
        self.num_requests_working += 1
        
        #num_prompt_tokens = len(text_prompt.split()) #estimate, and could switch to faster option if necessary
        num_prompt_tokens = len(text_prompt) / 4.0
        num_req_tokens_started = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working += num_req_tokens_started
        self.num_tokens_incoming += num_req_tokens_started
        self.total_prompt_tokens += num_prompt_tokens
        # self.cur_perf = self.num_requests_working * self.curr_tokens_per_second 
    
    def start_req(self, request):
        if request is None:
            print("metrics starting null request")
            return
        self._start_req(request["inputs"], request["parameters"])

    #undos what __start_req does
    def _error_req(self, text_prompt, parameters, code=None):
        self.num_requests_recieved -= 1
        self.num_requests_working -= 1
        if code is None or code != 422: #this means client side issue, so don't fault server
            #num_prompt_tokens = len(text_prompt.split())
            num_prompt_tokens = len(text_prompt) / 4.0
            num_req_tokens_started = num_prompt_tokens + parameters["max_new_tokens"]
            self.num_tokens_working -= num_req_tokens_started
            self.num_tokens_incoming -= num_req_tokens_started
            self.num_tokens_errored += num_req_tokens_started
            self.total_prompt_tokens -= num_prompt_tokens
            # self.cur_perf = self.num_requests_working * self.curr_tokens_per_second


    def error_req(self, request, code=None):
        if request is None:
            print("metrics error null request")
            return
        self._error_req(request["inputs"], request["parameters"], code)

    #confirms a successful request
    def _finish_req(self, text_prompt, parameters):
        self.num_requests_finished += 1
        self.num_requests_working -= 1

        #num_prompt_tokens = len(text_prompt.split())
        num_prompt_tokens = len(text_prompt) / 4.0
        num_req_tokens_finished = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working -= num_req_tokens_finished
        self.num_tokens_finished += num_req_tokens_finished
        
        
        # self.cur_perf = self.num_requests_working * self.curr_tokens_per_second
        self.cur_perf = self.num_requests_finished * self.curr_tokens_per_second  

        elapsed = time.time() - self.request_ltime
        self.request_ltime = time.time()

        alpha = 0.95       
        self.elapsed_avg        = alpha*self.elapsed_avg + (1-alpha)*elapsed
        self.tokens_per_req_avg = alpha*self.tokens_per_req_avg + (1-alpha)*num_req_tokens_finished
        #self.cur_perf           = self.tokens_per_req_avg / max(self.elapsed_avg, 0.00001)
        #print(f"cur_perf  {self.cur_perf} = {self.tokens_per_req_avg} / {self.elapsed_avg}")

    def finish_req(self, request):
        if request is None:
            print("metrics finishing null request")
            return
        self._finish_req(request["inputs"], request["parameters"])

    def report_batch_capacity(self, json_data):
        self.batch_capacity = json_data["max_batch_tokens"]
    
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