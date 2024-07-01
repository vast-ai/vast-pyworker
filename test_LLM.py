import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import time
import random

MAX_WORKERS = 256

def decode_line(line):
    payload = line.decode("utf-8")
    if payload.startswith("data:"):
        try: 
            json_payload = json.loads(payload.lstrip("data:").rstrip("/n"))
            if "token" in json_payload.keys():
                return json_payload["token"]["text"]
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
    
    return None

def worker(args, server_address, api_key, prompt_input):

    worker_address = args.worker_addr
    if (worker_address is None):
        # Call /route/ endpoint
        route_url = f"{server_address}/route/"
        route_payload = {
            "endpoint": args.endpoint_name,
            "api_key": api_key,
            "cost": 256
        }
        jdata = json.dumps(route_payload)
        print(f"calling {route_url} with {jdata}")
        response = requests.post(route_url, headers={"Content-Type": "application/json"}, data=jdata, timeout=4)

        if response.status_code != 200:
            print(f"Failed to get worker address for {route_url} response.status_code: {response.status_code}")
            return

        try:
            message = response.json()
            worker_address = message['url']
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            print(f"got reponse: {response.text}")
            return

        

    # Call /generate endpoint

    if args.generate_stream:
        print(f"calling {worker_address}/generate_stream")
        generate_url = f"{worker_address}/generate_stream"
    else:
        print(f"calling {worker_address}/generate")
        generate_url = f"{worker_address}/generate"

    generate_payload = {
        "token": "22e9c620e8c500dbf3ac880fa1b54242ab51a5420c1bd2af5d2450b489d46731",
    }

    if args.backend == "TGI":
        generate_payload["inputs"] = prompt_input
        generate_payload["parameters"] = {"max_new_tokens" : 256}
    elif args.backend == "OOBA":
        generate_payload["prompt"] = prompt_input
        generate_payload["max_new_tokens"] = 256
    else:
        print(f"unsupported backend: {args.backend}")
        return

    print(f"using payload: {generate_payload}")
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
    route_url = f"{server_address}/route/"
    route_payload = {
        "endpoint": args.endpoint_name,
        "api_key": api_key,
        "cost": 256
    }
    print(f"calling {route_url}")
    response = requests.post(route_url, headers={"Content-Type": "application/json"}, data=json.dumps(route_payload), timeout=4)

    if response.status_code != 200:
        print(f"Failed to get worker address for {route_url} response.status_code: {response.status_code}")
        return

    try:
        message = response.json()
        worker_address = message['url']
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        print(f"got reponse: {response.text}")
        return

    time.sleep(random.randint(0, 3))

    # Call /generate endpoint
    generate_payload = message
    if args.generate_stream:
        generate_url = f"{worker_address}/generate_stream"
    else:
        generate_url = f"{worker_address}/generate"

    if args.backend == "TGI":
        generate_payload["inputs"] = prompt_input
        generate_payload["parameters"] = {"max_new_tokens" : 256}
    elif args.backend == "OOBA":
        generate_payload["prompt"] = prompt_input
        generate_payload["max_new_tokens"] = 256
    else:
        print(f"unsupported backend: {args.backend}")
        return

    print(f"calling worker: {worker_address}, using payload: {generate_payload}")
    generate_response = requests.post(generate_url, headers={"Content-Type": "application/json"}, json=generate_payload, stream=args.generate_stream)

    if generate_response.status_code != 200:
        print(f"Failed to call /generate endpoint for {generate_url}, got status code: {generate_response.status_code}")
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
    parser.add_argument("api_key", help="API Key")
    parser.add_argument("endpoint_name", type=str, help="The name of the autoscaling group endpoint")
    parser.add_argument("prompt_input", help="Prompt input for /generate endpoint")
    parser.add_argument("N", type=int, help="Number of tasks")
    parser.add_argument("--server_address", help="Main server address", default="https://run.vast.ai")
    parser.add_argument("--use_auth", action="store_true", help="Whether to provide crypto message and signature to worker endpoint")
    parser.add_argument("--generate_stream", action="store_true", help="Whether to generate a streaming request or not")
    parser.add_argument("--worker_addr", help="worker address override", default=None)
    parser.add_argument("--rps", help="requests per second", default=1)
    parser.add_argument("--backend", help="Name of backend in use on worker server", default="TGI")
    args = parser.parse_args()

    futures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as e:
        for _ in range(args.N):
            if args.use_auth:
                future = e.submit(auth_worker, args, args.server_address, args.api_key, args.prompt_input)
            else:
                future = e.submit(worker, args, args.server_address, args.api_key, args.prompt_input)

            futures.append(future)
        
            time.sleep(1.0 / args.rps)

    for future in futures:
        future.result()

if __name__ == "__main__":
    main()
