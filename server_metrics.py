import sys
import time
import random
from threading import Thread
import threading
from abc import ABC, abstractmethod

from utils import post_request

class ServerMetrics(ABC):
    def __init__(self, id, control_server_url, send_server_data):
        self.id = int(id)
        self.control_server_url = control_server_url
        self.send_server_data = send_server_data
        self.overloaded = False
        
        self.num_requests_recieved = 0
        self.num_requests_finished = 0
        self.num_requests_working = 0

        self.cur_perf = 0.0
        self.max_perf = 1.0
        self.cur_capacity = 0.0
        self.cur_capacity_lastreport = 0.1234

        self.model_loaded = False
        self.loadtime = 0.0
        
        self.cur_load = 0.0
        self.fill_data_lut = 0.0

        self.update_interval = 1.0
        if self.send_server_data:
            self.t1 = Thread(target=self.send_data_loop)
            self.t1.start()

        print(f"ServerMetrics({id},{control_server_url})")

    def send_data_loop(self):
        while True:
            if self.send_data_condition():
                data = {"id" : self.id, "message" : "data update"}
                self.fill_data(data)
                self.send_data(data, self.control_server_url, "/worker_status/")
            time.sleep(self.update_interval)

    def send_data(self, data, url, path):
        full_path = url + path
        print(f'[server_metrics] sending data to url: {full_path}, data: {data}')
        thread = threading.Thread(target=post_request, args=(full_path,data))
        thread.start()
        sys.stdout.flush()
    
    def fill_data_generic(self, data):
        data["num_requests_working"] = self.num_requests_working
        data["overloaded"] = self.overloaded
        data["num_requests_recieved"] = self.num_requests_recieved
        data["cur_perf"]     = self.cur_perf

        if self.model_loaded:
            data["loadtime"] = self.loadtime
            data["max_perf"] = self.max_perf

    @abstractmethod
    def send_data_condition(self):
        pass
    
    @abstractmethod
    def fill_data(self, data):
        pass

    @abstractmethod
    def start_req(self, request):
        pass

    @abstractmethod
    def finish_req(self, request):
        pass

    @abstractmethod
    def report_req_stats(self, log_data):
        pass

    def report_loaded(self, log_data):
        self.model_loaded = True
        self.overloaded = False
        if "max_perf" in log_data.keys():
            self.max_perf   = log_data["max_perf"]
        if "loadtime" in log_data.keys():
            self.loadtime   = log_data["loadtime"]


class TGIServerMetrics(ServerMetrics):
    def __init__(self, id, control_server_url, send_server_data):
        self.batch_capacity = None
        self.total_prompt_tokens = 0.0
        
        self.num_tokens_working = 0
        self.num_tokens_finished = 0.0 # is periodically reset every interval
        self.curr_queue_time = 0.0
        self.curr_tokens_per_second = 0.0 # this is on a request by request basis, and doesn't take into account concurrent requests because of batching

        self.request_ltime = time.time()
        self.elapsed_avg = 1.0
        self.tokens_per_req_avg = 1024.0
        self.num_tokens_incoming = 0.0

        super().__init__(id, control_server_url, send_server_data)
    
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
        self.cur_load = self.num_tokens_incoming / elapsed
        data["cur_load"] = self.cur_load
        self.fill_data_lut = ntime
        self.num_tokens_incoming = 0
        
    def __start_req(self, text_prompt, parameters):
        self.num_requests_recieved += 1
        self.num_requests_working += 1
        
        num_prompt_tokens = len(text_prompt.split()) #estimate, and could switch to faster option if necessary
        num_req_tokens_started = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working += num_req_tokens_started
        self.num_tokens_incoming += num_req_tokens_started
        self.total_prompt_tokens += num_prompt_tokens
        self.cur_perf = self.num_requests_working * self.curr_tokens_per_second 
    
    def start_req(self, request):
        if request is None:
            print("metrics starting null request")
            return
        self.__start_req(request["inputs"], request["parameters"])

    #undos what __start_req does
    def __error_req(self, text_prompt, parameters):
        self.num_requests_recieved -= 1
        self.num_requests_working -= 1

        num_prompt_tokens = len(text_prompt.split())
        num_req_tokens_started = num_prompt_tokens + parameters["max_new_tokens"]
        self.num_tokens_working -= num_req_tokens_started
        self.num_tokens_incoming -= num_req_tokens_started
        self.total_prompt_tokens -= num_prompt_tokens
        self.cur_perf = self.num_requests_working * self.curr_tokens_per_second

    def error_req(self, request):
        if request is None:
            print("metrics error null request")
            return
        self.__error_req(request["inputs"], request["parameters"])

    #confirms a successful request
    def __finish_req(self, text_prompt, parameters):
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

    def finish_req(self, request):
        if request is None:
            print("metrics finishing null request")
            return
        self.__finish_req(request["inputs"], request["parameters"])

    def report_batch_capacity(self, json_data):
        self.batch_capacity = json_data["max_batch_tokens"]
    
    def report_req_stats(self, log_data):
        self.curr_queue_time = log_data["queue_time"]

        if "tokens_per_second" not in log_data.keys():
            tokens_per_second = 1 / log_data["time_per_token"]
            real_tokens_generated = int(log_data["inference_time"] * tokens_per_second)
        else:
            tokens_per_second = log_data["tokens_per_second"]
            real_tokens_generated = log_data["tokens_generated"]

        alpha = pow(0.5, real_tokens_generated / (4*1024))
        self.curr_tokens_per_second = alpha*self.curr_tokens_per_second + (1.0-alpha)*tokens_per_second
      
        # print(f"real_tokens_generated: {real_tokens_generated}   curr_tokens_per_second  {self.curr_tokens_per_second} = {alpha}*{self.curr_tokens_per_second} + {1.0-alpha}*{tokens_per_second}")

        if (log_data["queue_time"] > log_data["inference_time"]):
            self.overloaded = True
        else:
            self.overloaded = False

class OOBAServerMetrics(TGIServerMetrics):
    def __init__(self, id, control_server_url, send_server_data):
        super().__init__(id, control_server_url, send_server_data)

    def start_req(self, request):
        if request is None:
            print("metrics starting null request")
            return
        self.__start_req(request["prompt"], request)

    def finish_req(self, request):
        if request is None:
            print("metrics finishing null request")
            return
        self.__finish_req(request["prompt"], request)

    def error_req(self, request):
        if request is None:
            print("metrics error null request")
            return
        self.__error_req(request["prompt"], request)


class IMGServerMetrics(ServerMetrics):
    def __init__(self, id, control_server_url, send_server_data):
        self.total_prompt_tokens = 0
        self.tot_request_time = 0
        self.img_size = 512 * 512 #add this as a parameter

        super().__init__(id, control_server_url, send_server_data)
        
    def fill_data(self, data):
        self.fill_data_generic(data)
        data["cur_load"] = self.img_size * self.num_requests_working
        data["total_prompt_tokens"] = self.total_prompt_tokens
        self.cur_capacity_lastreport = self.total_prompt_tokens

    def start_req(self, request):
        self.num_requests_recieved += 1
        self.num_requests_working += 1

        num_prompt_tokens = len(request["prompt"].split())
        self.total_prompt_tokens += num_prompt_tokens

    def finish_req(self, request):
        self.num_requests_finished += 1
        self.num_requests_working -= 1

    def error_req(self, request):
        self.num_requests_recieved -= 1
        self.num_requests_working -= 1

        num_prompt_tokens = len(request["prompt"].split())
        self.total_prompt_tokens -= num_prompt_tokens

    def report_req_stats(self, log_data):
        self.tot_request_time += log_data["time_elapsed"]
        self.cur_perf = self.img_size * (self.num_requests_finished / self.tot_request_time)

    def send_data_condition(self):
        return (((random.randint(0, 9) == 3) or (self.total_prompt_tokens != self.cur_capacity_lastreport)) and self.model_loaded)

        
