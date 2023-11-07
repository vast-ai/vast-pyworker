from metrics import GenericMetrics

class Metrics(GenericMetrics):
    def __init__(self, id, control_server_url, send_server_data):
        super().__init__(id, control_server_url, send_server_data)

    def start_req(self, request):
        if request is None:
            print("metrics starting null request")
            return
        super()._start_req(request["prompt"], request)

    def finish_req(self, request):
        if request is None:
            print("metrics finishing null request")
            return
        super()._finish_req(request["prompt"], request)

    def error_req(self, request):
        if request is None:
            print("metrics error null request")
            return
        super()._error_req(request["prompt"], request)

    def report_req_stats(self, log_data):
        tokens_per_second = log_data["tokens_per_second"]
        real_tokens_generated = log_data["tokens_generated"]

        alpha = pow(0.5, real_tokens_generated / (4*1024))
        self.curr_tokens_per_second = alpha*self.curr_tokens_per_second + (1.0-alpha)*tokens_per_second