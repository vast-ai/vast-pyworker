import re
import json
import sys

from logwatch import GenericLogWatch
from test_model import ModelPerfTest
from utils import send_data

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

class LogWatch(GenericLogWatch):
    def __init__(self, id, control_server_url, master_token):
        perf_test = ModelPerfTest(backend_name="tgi")
        super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=perf_test)

        self.metric_names = ["time_per_token", "inference_time", "queue_time", "max_new_tokens"]
        self.batch_pattern = re.compile(r'Setting max batch total tokens to (\d+)')
        self.loading_line = "starting model download"
        
        self.sanity_file = "perf_sanity_tgi.json"

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
        data = {"id" : self.id, "mtoken" : self.master_token}
        data["max_batch_prefill_tokens"] = self.max_batch_prefill_tokens
        data["max_batch_tokens"] = self.max_batch_total_tokens
        data["max_capacity"] = self.max_batch_total_tokens
        send_data(data, self.control_server_url, "/worker_status/", "logwatch-tgi")
        send_data(data, self.auth_server_url, "/report_capacity", "logwatch-internal")
        
        self.perf_test.update_params(int(self.max_total_tokens * 0.75), int(self.max_batch_total_tokens * 0.75))

    
    def forward_server_data(self, line_metrics, generate_params):
        data = {"id" : self.id, "mtoken" : self.master_token}
        data["max_new_tokens"] = generate_params["max_new_tokens"]
        found = False 
        for metric_name in self.metric_names:
            if metric_name in line_metrics.keys():
                data[metric_name] = format_metric_value(line_metrics[metric_name])
                found = True

        if found:
            send_data(data, self.auth_server_url, "/report_done", "logwatch-internal")

    def send_error(self, error_msg):
        data = {"id" : self.id, "mtoken" : self.master_token}
        data["error_msg"] = error_msg
        send_data(data, self.control_server_url, "/worker_status/", "logwatch-tgi")
        send_data(data, self.auth_server_url, "/report_error", "logwatch-internal")


    def __handle_line(self, line_json):
        if "fields" in line_json.keys():
            if line_json["level"] == "ERROR":
                invalid_req_error = "`inputs` tokens + `max_new_tokens` must be <= 2048."
                if invalid_req_error not in line_json["message"]:
                    self.send_error(line_json["fields"]["message"])
                else:
                    print(f"invalid input error: {line_json['message']}")
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