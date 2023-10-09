import requests
import threading
import argparse
import json
import time
import random

def decode_line(line):
	payload = line.decode("utf-8")

	if payload.startswith("data:"):
		json_payload = json.loads(payload.lstrip("data:").rstrip("/n"))
		return json_payload["token"]["text"]
	else:
		return None

def worker(args, server_address, api_key, prompt_input):

    worker_address = args.worker_addr
    if (worker_address is None):
        # Call /queue_task/ endpoint
        queue_task_url = f"{server_address}/queue_task/"
        queue_task_payload = {
            "endpoint": args.endpoint_name,
            "api_key": api_key,
            "cost": 256
        }
        jdata = json.dumps(queue_task_payload)
        print(f"calling {queue_task_url} with {jdata}")
        response = requests.post(queue_task_url, headers={"Content-Type": "application/json"}, data=jdata, timeout=4)

        if response.status_code != 200:
            print(f"Failed to get worker address for {queue_task_url} response.status_code: {response.status_code}")
            return

        message = response.json()
        worker_address = message['url']
        #worker_address = response.text

    # Call /generate endpoint

    if args.generate_stream:
        print(f"calling {worker_address}/generate_stream")
        generate_url = f"{worker_address}/generate_stream"
    else:
        print(f"calling {worker_address}/generate")
        generate_url = f"{worker_address}/generate"

    generate_payload = {
        "token": "22e9c620e8c500dbf3ac880fa1b54242ab51a5420c1bd2af5d2450b489d46731",
        "inputs": prompt_input,
        "parameters": {"max_new_tokens": 256}
    }
    generate_response = requests.post(generate_url, headers={"Content-Type": "application/json"}, data=json.dumps(generate_payload), stream=args.generate_stream)

    if generate_response.status_code != 200:
        print(f"Failed to call /generate endpoint for {generate_url} {generate_response.status_code}")
        return

    if args.generate_stream:
        print(f"Starting streaming response from {generate_url}")
        for line in generate_response.iter_lines():
            if line == b"\n":
                continue

            line_token = decode_line(line)
            if line_token:
                print(line_token)

    else:
        print(f"Response from {generate_url}:", generate_response.text)

def auth_worker(args, server_address, api_key, prompt_input):
    queue_task_url = f"{server_address}/queue_task/"
    queue_task_payload = {
        "endpoint": args.endpoint_name,
        "api_key": api_key,
        "cost": 256
    }
    print(f"calling {queue_task_url}")
    response = requests.post(queue_task_url, headers={"Content-Type": "application/json"}, data=json.dumps(queue_task_payload), timeout=4)

    if response.status_code != 200:
        print(f"Failed to get worker address for {queue_task_url} response.status_code: {response.status_code}")
        return

    message = response.json()
    worker_address = message['url']

    time.sleep(random.randint(0, 3))

    # Call /generate endpoint
    generate_payload = message
    if args.generate_stream:
        generate_url = f"{worker_address}/generate_stream"
    else:
        generate_url = f"{worker_address}/generate"

    generate_payload["inputs"] = prompt_input
    generate_payload["parameters"] = {"max_new_tokens" : 256}

    print(f"calling worker: {worker_address}")
    generate_response = requests.post(generate_url, headers={"Content-Type": "application/json"}, json=generate_payload, stream=args.generate_stream)

    if generate_response.status_code != 200:
        print(f"Failed to call /generate endpoint for {generate_url}")
        return

    if args.generate_stream:
        print(f"Starting streaming response from {generate_url}")
        for line in generate_response.iter_lines():
            if line == b"\n":
                continue

            line_token = decode_line(line)
            if line_token:
                print(line_token)

    else:
        print(f"Response from {generate_url}:", generate_response.text)

def main():
    parser = argparse.ArgumentParser(description="Test inference endpoint")
    parser.add_argument("server_address", help="Main server address")
    parser.add_argument("api_key", help="API Key")
    parser.add_argument("endpoint_name", type=str, help="The name of the autoscaling group endpoint")
    parser.add_argument("prompt_input", help="Prompt input for /generate endpoint")
    parser.add_argument("N", type=int, help="Number of tasks")
    parser.add_argument("--use_auth", action="store_true", help="Whether to provide crypto message and signature to worker endpoint")
    parser.add_argument("--generate_stream", action="store_true", help="Whether to generate a streaming request or not")
    parser.add_argument("--worker_addr", help="worker address override", default=None)
    args = parser.parse_args()

    threads = []
    for _ in range(args.N):
        if args.use_auth:
            thread = threading.Thread(target=auth_worker, args=(args, args.server_address, args.api_key, args.prompt_input))
        else:
            thread = threading.Thread(target=worker, args=(args, args.server_address, args.api_key, args.prompt_input))
        thread.start()
        threads.append(thread)
        time.sleep(0.20)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
