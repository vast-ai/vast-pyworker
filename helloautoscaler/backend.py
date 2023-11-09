import time
from flask import abort

import notify

class Backend():
    def __init__(self, container_id, *args, **kwargs):
    
        t1 = time.time()
        self.id = container_id
        
        self.max_perf = 5.0
        self.count = 0
        self.num_requests_recieved = 0
        self.interval_requests_recieved = 0
        
        self.update_interval = 10
        t2 = time.time()

        notify.loaded(id=self.id, load_time=t2 - t1, max_perf=self.max_perf)
        
    def send_data_loop(self):
        while True:
            cur_load = self.interval_requests_recieved / self.update_interval
            notify.update(self.id, cur_load, self.num_requests_recieved)
            self.interval_requests_recieved = 0
            time.sleep(self.update_interval)

def increment_handler(backend, request):
    request_dict = request.json
    backend.num_requests_recieved += 1
    backend.interval_requests_recieved += 1
    if "amount" in request_dict.keys():
        backend.count += request_dict["amount"]        
        return "Incremented"
    
    abort(400)

def value_handler(backend, request):
    return {"value" : backend.count}

flask_dict = {
    "POST" : {
        "increment" : increment_handler
    },
    "GET" : {
        "value" : value_handler
    }
}