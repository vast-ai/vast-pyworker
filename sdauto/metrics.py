import random
import time

from metrics import GenericMetrics
from test_model import TOKENS_PER_WORD

def get_param(worker_payload, key, default):
    return worker_payload[key] if key in worker_payload.keys() else default

def calc_sdauto_work(worker_payload): #note that "load" metrics just have to be self-consitant within a usecase (such as stable-diffusion, LLMs, etc.) and not across them
    height = get_param(worker_payload, "height", 512)
    width = get_param(worker_payload, "width", 512)
    batch_size = get_param(worker_payload, "batch_size", 1)
    steps = get_param(worker_payload, "steps", 50)
    input_prompt = get_param(worker_payload, "prompt", "")
    input_tokens = len(input_prompt.split()) * TOKENS_PER_WORD
    alpha = 1
    return height * width * batch_size * steps + alpha * input_tokens

class Metrics(GenericMetrics):
    def __init__(self, id, master_token, control_server_url, send_server_data):
    
        self.tot_work_completed = 0
        self.finished_request_time = 0
        self.work_incoming = 0
        self.work_finished = 0
        self.work_errored  = 0

        self.perf = 0.0 
        
        super().__init__(id, master_token, control_server_url, send_server_data)
        
    def fill_data(self, data):
        self.fill_data_generic(data)

        ntime = time.time()
        elapsed = ntime - self.fill_data_lut
        if (self.fill_data_lut == 0.0):
            elapsed = 1.0
        self.fill_data_lut = ntime
        self.cur_load = (self.work_incoming + self.work_errored) / elapsed
        data["cur_load"] = self.cur_load     #self.img_size * self.num_requests_working
        # data["total_prompt_tokens"] = self.total_prompt_tokens
        self.work_incoming = 0
        self.work_errored  = 0
        # self.work_finished = 0 
        self.cur_capacity_lastreport = self.work_finished

    def start_req(self, request):
        self.num_requests_recieved += 1
        self.num_requests_working += 1
        self.work_incoming += calc_sdauto_work(request)

    def finish_req(self, request):
        self.num_requests_finished += 1
        self.num_requests_working -= 1
        self.finished_request_time += request["time_elapsed"]
        request_work = calc_sdauto_work(request)
        
        alpha = 0.5
        cur_perf = request_work / request["time_elapsed"] if request["time_elapsed"] != 0.0 else 0.0
        self.cur_perf = alpha * self.cur_perf + (1 - alpha) * cur_perf

        self.work_finished += request_work

    def error_req(self, request):
        self.num_requests_recieved -= 1
        self.num_requests_working -= 1
        self.work_incoming -= calc_sdauto_work(request)
        self.work_errored += calc_sdauto_work(request)

    def report_req_stats(self, log_data):
        # self.tot_request_time += log_data["time_elapsed"]
        
        self.curr_wait_time = log_data["wait_time"]

        # self.cur_perf = self.work_finished / self.finished_request_time if self.finished_request_time != 0.0 else 0.0
        # self.finished_request_time = 0.0

        if self.curr_wait_time > 30.0:
            self.overloaded = True
        else:
            self.overloaded = False

    def send_data_condition(self):
        return (((random.randint(0, 9) == 3) or (self.work_finished != self.cur_capacity_lastreport)) and self.model_loaded)