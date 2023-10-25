import sys
import os
import re

from logwatch import LogWatch
from test_model import ModelPerfTest

class LogWatchOOBA(LogWatch):
    def __init__(self, id, control_server_url, master_token, ready_pattern, update_pattern):
       super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, backend="OOBA")
       self.max_total_tokens = 1500
       self.max_batch_total_tokens = 25000 #have to estimate for now
       self.ready_pattern = ready_pattern
       self.update_pattern = update_pattern

    def estimate_model_params(self):
        perf_test = ModelPerfTest(self.max_total_tokens, self.max_batch_total_tokens, backend="OOBA")
        total_tokens = [1000, 1500, 2000]
        batch_total_tokens = [20000, 25000, 30000, 35000, 40000]
        for btt in batch_total_tokens:
            for tt in total_tokens:
                perf_test.update_params(tt, btt)
                perf_test.run(1)

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
            tps = match.group(1)
            tokens = match.group(2)
            update_params = {"tokens_per_second" : tps, "tokens_generated" : tokens}
            self.send_model_update(update_params)

        return False

    def send_model_update(self, update_params):
        data = {"id" : self.id, "mtoken" : self.master_token}
        for k,v in update_params.items():
            data[k] = v
        self.send_data(data, self.auth_server_url, "/report_done")

    def check_model_error(self):
        pass
     
def main():
    ready_pattern = re.compile(r'Loaded the model')
    update_pattern = re.compile(r'(\d+\.\d+) tokens/s, (\d+) tokens')
    lw = LogWatchOOBA(id=os.environ['CONTAINER_ID'], control_server_url=os.environ["REPORT_ADDR"], master_token=os.environ["MASTER_TOKEN"], ready_pattern=ready_pattern, update_pattern=update_pattern)
    
    print("[logwatch-ooba] ready and waiting for input\n")
    sys.stdout.flush()
    for line in sys.stdin:
        if lw.check_model_ready(line):
            continue
        elif lw.check_model_update(line):
            continue
        

if __name__ == "__main__":
    main()