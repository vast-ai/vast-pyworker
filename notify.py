from utils import send_data

notify_endpoint = "/worker_status/"

def loaded(data, autoscaler_address, load_time, max_perf):
    data["loadtime"] = load_time
    data["max_perf"] = max_perf
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def update(data, autoscaler_address, cur_load, num_requests_recieved):
    data["cur_load"] = cur_load
    data["num_requests_recieved"] = num_requests_recieved
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def error(data, autoscaler_address, error_msg):
    data["error_msg"] = error_msg
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")
