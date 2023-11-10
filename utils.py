import subprocess
import sys
import json
import requests
import time
import datetime

def get_curr_instances():
	result = subprocess.run(["vastai", "show", "instances", "--raw"], capture_output=True)
	instance_info = result.stdout.decode('utf-8')
	if instance_info:
		try:
			curr_instances = json.loads(instance_info)
		except json.decoder.JSONDecodeError:
			curr_instances = None
	else:
		curr_instances = None

	return curr_instances

def get_model_address(instance):
	addr = instance["public_ipaddr"] + ":" + instance["ports"]["3000/tcp"][0]["HostPort"]
	addr = addr.replace('\n', '')
	return addr

def send_data(data, url, path, sender):
    full_path = url + path
    if sender != "logwatch-internal":
        print(f'{datetime.datetime.now()} [{sender}] sending data to url: {full_path}, data: {data}')
        sys.stdout.flush()
    
    rcode = post_request(full_path, data)
    
    if sender != "logwatch-internal":
        print(f"{datetime.datetime.now()} [{sender}] Notification sent. Response: {rcode}")
        sys.stdout.flush()

def post_request(full_path, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(full_path, json=data, timeout=1)
            return response.status_code
        except requests.Timeout:
            print(f"{time.time()} Request timed out")
        except Exception as e:
            print(f"{time.time()} Error: {e}")
        if attempt < max_retries - 1:
            print(f"{time.time()} retrying post request")
            time.sleep(2)
        else:
            return 0


