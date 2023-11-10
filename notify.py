from utils import send_data

notify_endpoint = "/worker_status/"

def loaded(id, autoscaler_address, load_time, max_perf):
    data = {"id" : id, "loadtime" : load_time, "max_perf" : max_perf}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def update(id, autoscaler_address, cur_load, num_requests_recieved):
    data = {"id" : id, "cur_load" : cur_load, "num_requests_recieved" : num_requests_recieved}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def error(id, autoscaler_address, error_msg):
    data = {"id" : id, "error_msg" : error_msg}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")
    pass
