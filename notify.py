from utils import send_data

autoscaler_address = "http://run.vast.ai"
notify_endpoint = "worker_status"

def loaded(id, load_time, max_perf):
    data = {"id" : id, "loadtime" : load_time, "max_perf" : max_perf}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def update(id, cur_load, num_requests_recieved):
    data = {"id" : id, "cur_load" : cur_load, "num_requests_recieved" : num_requests_recieved}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")

def error(id, error_msg):
    data = {"id" : id, "error_msg" : error_msg}
    send_data(data=data, url=autoscaler_address, path=notify_endpoint, sender="notify")
    pass
