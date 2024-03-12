import re

from logwatch import GenericLogWatch
from test_model import ModelPerfTest

class LogWatch(GenericLogWatch):
    def __init__(self, id, control_server_url, master_token):
        perf_test = ModelPerfTest(backend_name="sdauto")
        super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=perf_test)
        max_load = 512 * 512
        self.perf_test.update_params(max_load / 4, max_load / 2, max_load / 2)
        self.ready_pattern = re.compile("Model loaded in (\d+\.\d+)s") # self.ready_pattern = re.compile("Uvicorn running on http://127.0.0.1:5000")
        self.update_pattern = re.compile("127.0.0.1 (\d+\.\d+)") # self.update_pattern = re.compile("200 http/1.1 POST /sdapi/v1/txt2img 127.0.0.1 (\d+\.\d+)")
        self.loading_line = "Loading weights"
    
    def check_model_ready(self, line):
        if self.ready_pattern.search(line):
            self.model_loaded()
            return True
        return False
        
    def check_model_update(self, line):
        match = self.update_pattern.search(line)
        if match:
            wait_time = float(match.group(1))
            update_params = {"wait_time" : wait_time}
            self.send_model_update(update_params)
            return True
        
        return False
   
    def handle_line(self, line):
        if self.check_model_ready(line):
            return
        elif self.check_model_update(line):
            return