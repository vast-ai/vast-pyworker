import requests
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import time
import random

def auth_worker(server_address, args):
    route_url = f"{server_address}/route/"
    route_payload = {
        "endpoint": args.endpoint_name,
        "api_key": args.api_key,
        "cost": 256
    }
    # print(f"calling {route_url}")
    response = requests.post(route_url, headers={"Content-Type": "application/json"}, data=json.dumps(route_payload), timeout=None)

    if response.status_code != 200:
        print(f"Failed to get worker address for {route_url} response.status_code: {response.status_code}")
        return False

    # print(response.text)
    return True

def test_worker(server_address):
    test_url = f"{server_address}/"
    test_payload = {}

    response = requests.get(test_url, headers={"Content-Type": "application/json"}, data=json.dumps(test_payload), timeout=0.2)

    if response.status_code != 200:
        print(f"Failed to get worker address for {test_url} response.status_code: {response.status_code}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Test inference endpoint")
    parser.add_argument("server_address", help="Main server address")
    parser.add_argument("api_key", help="API Key")
    parser.add_argument("endpoint_name", type=str, help="The name of the autoscaling group endpoint")
    parser.add_argument("N", type=int, help="Number of tasks")
    parser.add_argument("--basic", action="store_true", help="Whether to provide crypto message and signature to worker endpoint")
    args = parser.parse_args()

    futures = []
    t1 = time.time()
    with ThreadPoolExecutor() as e:
        for _ in range(args.N):
            if args.basic:
                future = e.submit(test_worker, args.server_address)
            else:
                future = e.submit(auth_worker, args.server_address, args)
            
            futures.append(future)


    success_count = 0
    exception_count = 0
    for future in futures:
        try:
            if future.result():
                success_count += 1
        except Exception as e:
            print(e)
            exception_count += 1
    t2 = time.time()

    print(f"returning, {success_count} / {args.N} requests succeeded, {exception_count} exceptions encountered, took: {t2 - t1}")

if __name__ == "__main__":
    main()