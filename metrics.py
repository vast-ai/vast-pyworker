import sys
import time
from threading import Thread
import threading
from abc import ABC, abstractmethod

from utils import post_request

class GenericMetrics(ABC):
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
    def error_req(self, request):
        pass

    @abstractmethod
    def finish_req(self, request):
        pass

    def report_loaded(self, log_data):
        self.model_loaded = True
        self.overloaded = False
        if "max_perf" in log_data.keys():
            self.max_perf   = log_data["max_perf"]
        if "loadtime" in log_data.keys():
            self.loadtime   = log_data["loadtime"]





        
