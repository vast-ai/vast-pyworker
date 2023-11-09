import sys
import psutil
import time
import threading
from abc import ABC, abstractmethod
import datetime

from utils import send_data

class GenericMetrics(ABC):
    def __init__(self, id, control_server_url, send_server_data):
        self.id = int(id)
        self.control_server_url = control_server_url
        self.send_server_data = send_server_data
        self.overloaded = False
        self.error = False
        
        self.num_requests_recieved = 0
        self.num_requests_finished = 0
        self.num_requests_working = 0

        self.cur_perf = 0.0
        self.max_perf = 1.0
        self.cur_capacity = 0.0
        self.cur_capacity_lastreport = 0.1234

        self.model_loading = False
        self.model_loaded = False
        self.base_disk_usage = 0.0
        self.last_disk_usage = 0.0
        self.loadtime = 0.0
        
        self.cur_load = 0.0
        self.fill_data_lut = 0.0

        self.update_interval = 1.0
        if self.send_server_data:
            self.t1 = threading.Thread(target=self.send_data_loop)
            self.t1.start()

        print(f"{datetime.datetime.now()} ServerMetrics({id},{control_server_url})")

    def send_data_loop(self):
        while not self.error:
            if not self.model_loaded and self.model_loading:
                data = {"id" : self.id, "message" : "loading update"}
                self.update_loading(data)
                threading.Thread(target=send_data, args=(data, self.control_server_url, "/worker_status/", "metrics")).start()
                time.sleep(self.update_interval * 10)
            elif not self.model_loading and self.send_data_condition():
                data = {"id" : self.id, "message" : "data update"}
                self.fill_data(data)
                threading.Thread(target=send_data, args=(data, self.control_server_url, "/worker_status/", "metrics")).start()
            time.sleep(self.update_interval)
    
    def update_loading(self, data):
        new_usage = psutil.disk_usage('/').used
        data["disk_usage"] = new_usage
        data["additional_disk_usage"] = new_usage - self.last_disk_usage
        self.last_disk_usage = new_usage
    
    def fill_data_generic(self, data):
        data["num_requests_working"] = self.num_requests_working
        data["overloaded"] = self.overloaded
        data["num_requests_recieved"] = self.num_requests_recieved
        data["cur_perf"]     = self.cur_perf
        data["error"]        = self.error

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

    def report_loading(self, log_data):
        self.base_disk_usage = psutil.disk_usage('/').used
        self.last_disk_usage = self.base_disk_usage
        self.model_loading = True
    
    def report_loaded(self, log_data):
        self.model_loaded = True
        self.overloaded = False
        if "loadtime" in log_data.keys():
            self.loadtime   = log_data["loadtime"]
        
        if "max_perf" in log_data.keys():
            self.model_loading = False #perf test done
            self.max_perf   = log_data["max_perf"]
        
    def report_error(self, log_data):
        self.error = True
        self.error_msg = log_data["error_msg"]





        
