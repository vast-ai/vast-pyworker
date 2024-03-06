import requests
import json
import time
import random
from collections import defaultdict
from test_model import make_random_prompt, payload_dict


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

def get_worker(server_address, endpoint_name, cost, api_key, latency=None):
    route_url = f"{server_address}/route/"
    route_payload = {
        "endpoint": endpoint_name,
        "api_key": api_key,
        "cost": cost,
    }
    if latency:
        route_payload["latency"] = latency
    # print(f"calling {route_url}")
    response = requests.post(route_url, headers={"Content-Type": "application/json"}, data=json.dumps(route_payload), timeout=None)

    if response.status_code != 200:
        print(f"Failed to get worker address for {route_url} response.status_code: {response.status_code}")
        return

    try:
        worker_payload = response.json()
        if "url" in worker_payload.keys():
            return worker_payload
        else:
            print(f"no rdy workers ... endpoint status: {worker_payload['status']}")
            return
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        print(f"got reponse: {response.text}")
        return

def tgi_addr(worker_address, stream):
    if stream:
        return f"{worker_address}/generate_stream"
    else:
        return f"{worker_address}/generate"

def sdauto_addr(worker_address, stream):
    return f"{worker_address}/sdapi/v1/txt2img"

addr_dict = {
    "tgi" : tgi_addr,
    "sdauto" : sdauto_addr
}

latency_dict = {
    "tgi" : None,
    "sdauto" : 40.0
}

def auth_worker(endpoint_name, backend, worker_metric_map, api_key, input_cost, output_cost, server_address="https://run.vast.ai", worker_address=None, generate_stream=False):
    if worker_address is None:
        worker_payload = get_worker(server_address, endpoint_name, input_cost + output_cost, api_key, latency=latency_dict[backend])
        if worker_payload is None:
            return
        worker_address = worker_payload['url']
    else:
        worker_payload = {}
    
    # Call /generate endpoint
    prompt_input = make_random_prompt(input_cost)
    generate_url = addr_dict[backend](worker_address, generate_stream)
    payload_dict[backend](worker_payload, prompt_input, output_cost)
   
    if worker_address not in worker_metric_map.keys():
        worker_metric_map[worker_address] = defaultdict(int)

    worker_metric_map[worker_address]["reqs_sent"] += 1

    try:
        # print(f"calling worker: {worker_address}, using payload: {worker_payload}")
        generate_response = requests.post(generate_url, headers={"Content-Type": "application/json"}, json=worker_payload, stream=generate_stream)
    except Exception as e:
        print(f"requests error: {e}")
        return

    if generate_response.status_code != 200:
        print(f"Failed to call {endpoint_name} endpoint for {generate_url}, got status code: {generate_response.status_code}")
        worker_metric_map[worker_address]["reqs_failed"] += 1
        return False

    if generate_stream:
        # print(f"Starting streaming response from {generate_url}")
        for line in generate_response.iter_lines():
            if line == b"\n":
                continue

            line_token = decode_line(line)
            if line_token:
                pass
                # print(line_token)

    # else:
    #     print(f"Response from {generate_url}:", generate_response.text)
    
    response_words = len(generate_response.text.split())
    # print(f"got response of len: {response_words}")
    worker_metric_map[worker_address]["reqs_succeeded"] += 1
    return response_words


