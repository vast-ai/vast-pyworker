import sys
import os
import time
import datetime
import json
import re
from abc import ABC, abstractmethod
import importlib

from utils import send_data

class GenericLogWatch(ABC):
    def __init__(self, id, control_server_url, master_token, perf_test):
        self.id = id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.perf_test = perf_test

        self.auth_server_url = f"http://0.0.0.0:{os.environ['AUTH_PORT']}"

        self.start_time = time.time()

        self.max_total_tokens = None
        self.max_batch_total_tokens = None
        self.loading = False
        self.loading_line = "starting model download"

        self.perf_file = "perf_results.json"
        self.sanity_file = "perf_sanity.json"

    def send_model_update(self, update_params):
        data = {"id" : self.id, "mtoken" : self.master_token}
        for k,v in update_params.items():
            data[k] = v
        send_data(data, self.auth_server_url, "/report_done", "logwatch-internal")
    
    def metrics_sanity_check(self, throughput, avg_latency):
        if os.path.exists(self.sanity_file):
            with open(self.sanity_file, "r") as f:
                bounds = json.load(f)
            if throughput < bounds["max_throughput"] and avg_latency > bounds["min_avg_latency"]:
                return True
        else:
            print(f"Couldn't find sanity file: {self.sanity_file}")
        
        return False
    
    def load_perf_results(self, data):
        with open(self.perf_file, "r") as f:
            sys.stdout.flush()
            results = json.load(f)
            throughput, avg_latency = results["throughput"], results["avg_latency"]
            data["max_perf"] = throughput
            data["avg_latency"] = avg_latency
            print(f"{datetime.datetime.now()} [logwatch] loaded model perf test results: {throughput} {avg_latency} ")
            sys.stdout.flush()

    def run_perf_test(self, data):
        if self.perf_test is None:
            print(f"{datetime.datetime.now()} [logwatch] perf test hasn't been set up")
            return
        
        print(f"{datetime.datetime.now()} [logwatch] starting model perf test")
        sys.stdout.flush()
        sanity_check = self.perf_test.first_run()
        if sanity_check:
            print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest sanitycheck ")
            sys.stdout.flush()
            success, throughput, avg_latency = self.perf_test.run(3) #3
            if success:
                if self.metrics_sanity_check(throughput, avg_latency):
                    print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest performance metrics {success} {throughput} {avg_latency} in bounds")
                    with open(self.perf_file, "w") as f:
                        json.dump({"throughput" : throughput, "avg_latency" : avg_latency}, f)
                    data["max_perf"] = throughput
                    data["avg_latency"] = avg_latency
                else:
                    print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest performance metrics {success} {throughput} {avg_latency} out of bounds")
                    sys.stdout.flush()
                    data["error_msg"] = "performance metrics out of bounds"
            else:
                print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest not all test requests succeeded")
                sys.stdout.flush()
                data["error_msg"] = "not all test requests succeeded"
        else:
            print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest initial performance test took too long")
            sys.stdout.flush()
            data["error_msg"] = "initial performance test failed"
                
    def check_loading(self, line):
        if re.search(self.loading_line, line):
            self.loading = True
            send_data({"mtoken" : self.master_token}, self.auth_server_url, "/report_loading", "logwatch-internal")
            return True
        return False

    def model_loaded(self):
        print("[logwatch] starting model_loaded")
        sys.stdout.flush()
        
        end_time = time.time()
        data = {"id" : self.id, "mtoken" : self.master_token}
        data["loaded"] = True
        data["loadtime"] = end_time - self.start_time
        data["cur_perf"] = 0.0

        send_data(data, self.auth_server_url, "/report_loaded", "logwatch-internal") #so that it stops sending loading update messages
        if self.perf_test:
            if os.path.exists(self.perf_file):
                self.load_perf_results(data)
            else:
                self.run_perf_test(data)
            
            del self.perf_test

        print("[logwatch] sending data for model_loaded")
        sys.stdout.flush()     
        send_data(data, self.auth_server_url, "/report_loaded", "logwatch-internal") #to give model performance update
        send_data(data, self.control_server_url, "/worker_status/", "logwatch")
        

    @abstractmethod
    def handle_line(self, line):
        pass

def main():
    if not os.path.exists(f"{os.environ['BACKEND']}/logwatch.py"):
        print(f"[logwatch] logwatch.py doesn't exist for backend: {os.environ['BACKEND']}, skipping activation")
        return
    logwatch_lib = importlib.import_module(f"{os.environ['BACKEND']}.logwatch")
    logwatch_class = getattr(logwatch_lib, "LogWatch")
    lw = logwatch_class(id=os.environ['CONTAINER_ID'], control_server_url=os.environ["REPORT_ADDR"], master_token=os.environ["MASTER_TOKEN"])
    print("[logwatch] ready and waiting for input\n")
    sys.stdout.flush()
    for line in sys.stdin:
        if not lw.loading:
            if lw.check_loading(line):
                continue

        lw.handle_line(line)
        
        
if __name__ == "__main__":
    main()