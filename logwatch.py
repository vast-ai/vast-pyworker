import sys
import os
import time
import datetime
import json
import re
from abc import ABC, abstractmethod

from utils import post_request
from test_model import ModelPerfTest

class LogWatch(ABC):
    def __init__(self, id, control_server_url, master_token, perf_test):
        self.id = id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.perf_test = perf_test

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
                
    def model_loaded(self):
        print("[logwatch] starting model_loaded")
        sys.stdout.flush()
        end_time = time.time()
        data = {"id" : self.id, "mtoken" : self.master_token}
        data["loaded"] = True
        data["loadtime"] = end_time - self.start_time
        data["cur_perf"] = 0.0

        if self.perf_test:
            if os.path.exists(self.perf_file):
                self.load_perf_results(data)
            else:
                self.run_perf_test(data)
            
            del self.perf_test

        print("[logwatch] sending data for model_loaded")
        sys.stdout.flush()     
        self.send_data(data, self.control_server_url, "/worker_status/")
        self.send_data(data, self.auth_server_url, "/report_loaded")

    @abstractmethod
    def handle_line(self, line):
        pass

def format_metric_value(metric_str):
    if metric_str[-2:] == "ms":
        return (float(metric_str[:-2]) / 1.0e3)

    elif ord(metric_str[-2]) == 181: #mu
        return (float(metric_str[:-2]) / 1.0e6)

    elif metric_str[-1:] == "s":
        return (float(metric_str[:-1]))

    else:
        return metric_str
    
def parse_config(config):
    config = config.replace('{ ', '{"').replace(':', '":').replace(', ', ', "').replace(' }', '}').replace('Some("', '"').replace('")', '"').replace('Some(', '"').replace(')', '"').replace(': None', ': null')
    return json.loads(config)


class LogWatchTGI(LogWatch):
    def __init__(self, id, control_server_url, master_token):
        perf_test = ModelPerfTest(backend="TGI")
        super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=perf_test)

        self.metric_names = ["time_per_token", "inference_time", "queue_time", "max_new_tokens"]
        self.batch_pattern = re.compile(r'Setting max batch total tokens to (\d+)')

        self.max_batch_prefill_tokens = None
        
    
    def check_model_config(self, line):
        pass

    def read_config(self, config_info_line):
        self.max_batch_prefill_tokens = config_info_line['max_batch_prefill_tokens']
        self.max_total_tokens = config_info_line['max_total_tokens']

    def read_batch_capacity(self, batch_info_line):
        match = self.batch_pattern.search(batch_info_line)
        if match:
            self.max_batch_total_tokens = int(match.group(1))
            return True
        
        return False
            
    def send_capacity(self):
        data = {"id" : self.id}
        data["max_batch_prefill_tokens"] = self.max_batch_prefill_tokens
        data["max_batch_tokens"] = self.max_batch_total_tokens
        data["max_capacity"] = self.max_batch_total_tokens
        self.send_data(data, self.control_server_url, "/worker_status/")

        data["mtoken"] = self.master_token
        self.send_data(data, self.auth_server_url, "/report_capacity")
        
        self.perf_test.update_params(self.max_total_tokens, self.max_batch_total_tokens)

    
    def forward_server_data(self, line_metrics, generate_params):
        data = {"id" : self.id}

        data["max_new_tokens"] = generate_params["max_new_tokens"]
        found = False 
        for metric_name in self.metric_names:
            if metric_name in line_metrics.keys():
                data[metric_name] = format_metric_value(line_metrics[metric_name])
                found = True

        if found:
            data["mtoken"] = self.master_token
            self.send_data(data, self.auth_server_url, "/report_done")

    def send_error(self, error_msg):
        data = {"id" : self.id, "error_msg" : error_msg}
        self.send_data(data, self.control_server_url, "/worker_status/")

    def __handle_line(self, line_json):
        if "fields" in line_json.keys():
            if line_json["level"] == "ERROR":
                self.send_error(line_json["fields"]["message"])
            elif line_json["fields"]["message"][:4] == "Args":               
                tgi_args = line_json["fields"]["message"][4:]
                config = parse_config(tgi_args)
                print(config)
                sys.stdout.flush()
                self.read_config(config)
        if "message" in line_json.keys():
            if line_json["message"] == "Connected" and line_json["target"] == "text_generation_router":
                self.model_loaded()
            elif line_json["message"] == "Success" and line_json["target"] == "text_generation_router::server":
                generate_params = parse_config(line_json["span"]["parameters"][18:])
                self.forward_server_data(line_json["span"], generate_params)
            else:
                found = self.read_batch_capacity(line_json["message"])
                if found:
                    self.send_capacity()

    def handle_line(self, line):
        try:
            line_json = json.loads(line)
        except Exception as e:
            print(f"exception: {str(e)} parsing {line} ")
            return
            
        try:
            self.__handle_line(line_json)
        except Exception as e:
            print(f"exception: {str(e)} handling {line_json} ")
            return

class LogWatchOOBA(LogWatch):
    def __init__(self, id, control_server_url, master_token):
       perf_test = ModelPerfTest(backend="OOBA")
       super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=perf_test)
       self.max_total_tokens = 1500
       self.max_batch_total_tokens = 25000 #have to estimate for now
       self.ready_pattern = re.compile(r'Loaded the model')
       self.update_pattern = re.compile(r'(\d+\.\d+) tokens/s, (\d+) tokens')

    def estimate_model_params(self):
        if self.perf_test is None:
            print("no perf test loaded")
            return
        total_tokens = [1000, 1500, 2000]
        batch_total_tokens = [20000, 25000, 30000, 35000, 40000]
        for btt in batch_total_tokens:
            for tt in total_tokens:
                self.perf_test.update_params(tt, btt)
                self.perf_test.run(1)

    def check_model_config(self, line): 
        pass
    
    def check_model_ready(self, line):
        if self.ready_pattern.search(line):
            self.model_loaded()
            # self.estimate_model_params()
            return True
        return False

    def check_model_update(self, line):
        match = self.update_pattern.search(line)
        if match:
            tps = match.group(1)
            tokens = match.group(2)
            update_params = {"tokens_per_second" : tps, "tokens_generated" : tokens}
            self.send_model_update(update_params)

        return False

    def send_model_update(self, update_params):
        data = {"id" : self.id, "mtoken" : self.master_token}
        for k,v in update_params.items():
            data[k] = v
        self.send_data(data, self.auth_server_url, "/report_done")

    def check_model_error(self):
        pass

    def handle_line(self, line):
        if self.check_model_ready(line):
            return
        elif self.check_model_update(line):
            return

class LogWatchSDAUTO(LogWatch):
    def __init__(self, id, control_server_url, master_token):
        super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=None)
        self.ready_pattern = re.compile("Model loaded in (\d+\.\d+)s")
    
    def check_model_ready(self, line):
        if self.ready_pattern.search(line):
            self.model_loaded()
            return True
        return False
   
    def handle_line(self, line):
        self.check_model_ready(line)

watch_dict = {"TGI" : LogWatchTGI, "OOBA" : LogWatchOOBA, "SDAUTO" : LogWatchSDAUTO}

def main():
    lw = watch_dict[os.environ['BACKEND']](id=os.environ['CONTAINER_ID'], control_server_url=os.environ["REPORT_ADDR"], master_token=os.environ["MASTER_TOKEN"])
    print("[logwatch] ready and waiting for input\n")
    sys.stdout.flush()
    for line in sys.stdin:
        lw.handle_line(line)
        
if __name__ == "__main__":
    main()