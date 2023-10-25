import sys
import os
import time
import datetime
import json

from test_model import ModelPerfTest
from utils import post_request

class LogWatch:
    def __init__(self, id, control_server_url, master_token, backend):
        self.id = id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.backend = backend

        self.auth_server_url = f"http://0.0.0.0:{os.environ['AUTH_PORT']}"

        self.start_time = time.time()

        self.max_total_tokens = None
        self.max_batch_total_tokens = None
        
        self.perf_file = "perf_results.json"
        self.sanity_file = "perf_sanity.json"

    def send_data(self, data, url, path):
        full_path = url + path
        if ("loaded" in data.keys() or "error_msg" in data.keys() or "tokens_per_second" in data.keys()):
            print(f'{datetime.datetime.now()} [logwatch] sending data to url: {full_path}, data: {data}')
            sys.stdout.flush()
        
        rcode = post_request(full_path, data)

        if ("loaded" in data.keys() or "error_msg" in data.keys() or "tokens_per_second" in data.keys()):
            print(f"{datetime.datetime.now()} logwatch] Notification sent. Response: {rcode}")
            sys.stdout.flush()
    
    def metrics_sanity_check(self, throughput, avg_latency):
        if os.path.exists(self.sanity_file):
            with open(self.sanity_file, "r") as f:
                bounds = json.load(f)
            if throughput < bounds["max_throughput"] and avg_latency > bounds["min_avg_latency"]:
                return True
        else:
            print(f"Couldn't find sanity file: {self.sanity_file}")
        
        return False

    # def get_url(self):
    #     internal_port = os.environ['AUTH_PORT']
    #     port_var = f"VAST_TCP_PORT_{internal_port}"
    #     return f"http://{os.environ['PUBLIC_IPADDR']}:{os.environ[port_var]}"
    
    def model_loaded(self):
        print("[logwatch] starting model_loaded")
        sys.stdout.flush()
        end_time = time.time()
        data = {"id" : self.id}
        data["loaded"] = True
        data["loadtime"] = end_time - self.start_time
        # data["url"] = self.get_url()
        data["cur_perf"] = 0.0

        if os.path.exists(self.perf_file):
            with open(self.perf_file, "r") as f:
                sys.stdout.flush()
                results = json.load(f)
                throughput, avg_latency = results["throughput"], results["avg_latency"]
                data["max_perf"] = throughput
                data["avg_latency"] = avg_latency
                print(f"{datetime.datetime.now()} [logwatch] loaded model perf test results: {throughput} {avg_latency} ")
        else:
            print(f"{datetime.datetime.now()} [logwatch] starting model perf test with max_total_tokens: {self.max_total_tokens}, max_batch_total_tokens: {self.max_batch_total_tokens}")
            sys.stdout.flush()
            perf_test = ModelPerfTest(self.max_total_tokens, self.max_batch_total_tokens, backend=self.backend)
            sys.stdout.flush()
            sanity_check = perf_test.first_run()
            if sanity_check:
                print(f"{datetime.datetime.now()} [logwatch] ModelPerfTest sanitycheck ")
                sys.stdout.flush()
                success, throughput, avg_latency = perf_test.run(3)
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
                data["error_msg"] = "initial performance test took too long"
                    
            del perf_test
        
        self.send_data(data, self.control_server_url, "/worker_status/")

        