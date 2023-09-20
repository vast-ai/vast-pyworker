import sys
import re
import requests
import argparse
import json
import time
import os

def format_metric_value(metric_str):
    if metric_str[-2:] == "ms":
        return (float(metric_str[:-2]) / 1.0e3)

    elif ord(metric_str[-2]) == 181: #mu
        return (float(metric_str[:-2]) / 1.0e6)

    elif metric_str[-1:] == "s":
        return (float(metric_str[:-1]))

    else:
        return metric_str

class LogWatch:
    def __init__(self, id, control_server_url, master_token, metric_names, batch_pattern):
        self.id = int(id)
        self.control_server_url = control_server_url
        self.master_token = master_token
        # self.auth_server_url = self.get_url()
        self.auth_server_url = "http://0.0.0.0:3000"
        self.start_time = time.time() #this could be made more precise
        self.metric_names = metric_names
        self.batch_pattern = batch_pattern
        self.url = self.auth_server_url

        self.max_batch_tokens = None
        self.max_batch_prefill_tokens = None

    def get_url(self):
        internal_port = os.environ['AUTH_PORT']
        port_var = f"VAST_TCP_PORT_{internal_port}"
        return f"http://{os.environ['PUBLIC_IPADDR']}:{os.environ[port_var]}"
        
    def send_data(self, data, url, path):
        data["mtoken"] = self.master_token
        full_path = url + path
        print(f'[logwatch] sending data to url: {full_path}, data: {data}')
        sys.stdout.flush()
        response = requests.post(full_path, json = data)
        print(f"[logwatch] Notification sent. Response: {response.status_code}")
        sys.stdout.flush()

    def read_config(self, config_info_line):
        self.max_batch_prefill_tokens = config_info_line['max_batch_prefill_tokens']

    def read_batch_capacity(self, batch_info_line):
        match = self.batch_pattern.search(batch_info_line)
        if match:
            self.max_batch_tokens = int(match.group(1))
            return True
        
        return False
            
    def send_capacity(self):
        data = {"id" : self.id}
        data["max_batch_prefill_tokens"] = self.max_batch_prefill_tokens
        data["max_batch_tokens"] = self.max_batch_tokens
        self.send_data(data, self.auth_server_url, "/report_capacity")

    def forward_server_data(self, line_metrics):
        data = {"id" : self.id}

        found = False 
        for metric_name in self.metric_names:
            if metric_name in line_metrics.keys():
                data[metric_name] = format_metric_value(line_metrics[metric_name])
                found = True

        if found:
            self.send_data(data, self.auth_server_url, "/report_done")

    def notify_server_ready(self):
        end_time = time.time()
        data = {"id" : self.id}
        data["loaded"] = True
        data["loadtime"] = end_time - self.start_time
        data["url"] = self.url

        self.send_data(data, self.control_server_url, "/worker_status/")

def main():
    metric_names = ["time_per_token", "inference_time", "queue_time"]
    batch_pattern = re.compile(r'Setting max batch total tokens to (\d+)')

    watch = LogWatch(id=os.environ['CONTAINER_ID'], control_server_url=os.environ["REPORT_ADDR"], master_token=os.environ["MASTER_TOKEN"], metric_names=metric_names, batch_pattern=batch_pattern)

    print("[logwatch] ready and waiting for input\n")
    for line in sys.stdin:
        line_json = json.loads(line)
        if "fields" in line_json.keys():
            if line_json["fields"]["message"][:4] == "Args":
                tgi_args = line_json["fields"]["message"][4:]
                tgi_args = tgi_args.replace('{ ', '{"').replace(':', '":').replace(', ', ', "').replace(' }', '}').replace('Some(', '').replace(')', '').replace(': None', ': null')
                watch.read_config(json.loads(tgi_args))
        if "message" in line_json.keys():
            if line_json["message"] == "Connected" and line_json["target"] == "text_generation_router":
                watch.notify_server_ready()
            elif line_json["message"] == "Success" and line_json["target"] == "text_generation_router::server":
                watch.forward_server_data(line_json["span"])
            else:
                found = watch.read_batch_capacity(line_json["message"])
                if found:
                    watch.send_capacity()

if __name__ == "__main__":
    main()
