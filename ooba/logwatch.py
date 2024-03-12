import re

from logwatch import GenericLogWatch
from test_model import ModelPerfTest

class LogWatch(GenericLogWatch):
    def __init__(self, id, control_server_url, master_token):
       perf_test = ModelPerfTest(backend_name="ooba")
       super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=perf_test)
       self.max_total_tokens = 1500
       self.max_batch_total_tokens = 25000 #have to estimate for now
       self.perf_test.update_params(int(self.max_total_tokens * 0.75), self.max_total_tokens, int(self.max_batch_total_tokens * 0.75))
       self.ready_pattern = re.compile(r'Loaded the model')
       self.update_pattern = re.compile(r'(\d+\.\d+) tokens/s, (\d+) tokens')

    def estimate_model_params(self):
        if self.perf_test is None:
            print("no perf test loaded")
            return
        total_tokens = [1000, 1500, 2000]
        batch_total_tokens = [20000, 25000, 30000, 35000, 40000]
        for btt in batch_total_tokens:
            for tt in total_tokens:
                self.perf_test.update_params(tt, btt)
                self.perf_test.run(1)

    def check_model_config(self, line): 
        pass
    
    def check_model_ready(self, line):
        if self.ready_pattern.search(line):
            self.model_loaded()
            # self.estimate_model_params()
            return True
        return False

    def check_model_update(self, line):
        match = self.update_pattern.search(line)
        if match:
            tps = float(match.group(1))
            tokens = float(match.group(2))
            update_params = {"tokens_per_second" : tps, "tokens_generated" : tokens}
            self.send_model_update(update_params)
            return True

        return False

    def check_model_error(self):
        pass

    def handle_line(self, line):
        if self.check_model_ready(line):
            return
        elif self.check_model_update(line):
            return