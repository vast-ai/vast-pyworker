import sys
import os
import time
import re

from test_model import ModelPerfTest
from utils import post_request

class LogWatch:
    def __init__(self, id, control_server_url, master_token):
        self.id = id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.start_time = time.time()

    def model_loaded(self):
        print("model loaded")
        sys.stdout.flush()
        data = {"id" : self.id}
        data["loadtime"] = time.time() - self.start_time

        perf_test = ModelPerfTest(max_total_tokens=1000, max_batch_total_tokens=10000, backend="OOBA")
        print("set up perf test")
        sys.stdout.flush()
        time.sleep(2)
        sanity_check = perf_test.first_run()
        print("finished perf test")
        sys.stdout.flush()
        
        # post_request(self.control_server_url + "/worker_status/", data)

        
def main():
    lw = LogWatch(id=os.environ['CONTAINER_ID'], control_server_url=os.environ["REPORT_ADDR"], master_token=os.environ["MASTER_TOKEN"])
    loaded_pattern = re.compile(r'Loaded the model')
    print("[logwatch-ooba] ready and waiting for input\n")
    sys.stdout.flush()
    for line in sys.stdin:
        if loaded_pattern.search(line):
            lw.model_loaded()

if __name__ == "__main__":
    main()