import time
import threading
from flask import abort

import notify

class Backend():
    def __init__(self, container_id, master_token, control_server_url, send_data):
    
        t1 = time.time()
        self.id = container_id
        self.master_token = master_token
        self.control_server_url = control_server_url
        
        self.count = 0
        self.num_requests_recieved = 0
        self.interval_requests_recieved = 0
        
        t2 = time.time()

        data = {"id" : self.id, "mtoken" : self.master_token}
        notify.loaded(data=data, autoscaler_address=self.control_server_url, load_time=t2 - t1, max_perf=0.5)

        self.update_interval = 10
        t1 = threading.Thread(target=self.send_data_loop)
        t1.start()
        
    def send_data_loop(self):
        while True:
            cur_load = self.interval_requests_recieved / self.update_interval
            data = {"id" : self.id, "mtoken" : self.master_token}
            notify.update(data, self.control_server_url, cur_load, self.num_requests_recieved)
            self.interval_requests_recieved = 0
            time.sleep(self.update_interval)

    def track_request(self):
        self.num_requests_recieved += 1
        self.interval_requests_recieved += 1

def increment_handler(backend, request):
    backend.track_request()
    request_dict = request.json
    if "amount" in request_dict.keys():
        backend.count += request_dict["amount"]        
        return "Incremented"
    
    abort(400)

def value_handler(backend, request):
    backend.track_request()
    return {"value" : backend.count}

flask_dict = {
    "POST" : {
        "increment" : increment_handler
    },
    "GET" : {
        "value" : value_handler
    }
}