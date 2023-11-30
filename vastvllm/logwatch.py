import re

from logwatch import GenericLogWatch

class LogWatch(GenericLogWatch):
    def __init__(self, id, control_server_url, master_token):
        super().__init__(id=id, control_server_url=control_server_url, master_token=master_token, perf_test=None)
        self.update_pattern = re.compile(r"INFO")

    def extract_token_details(log_line, data):
        tokens_per_second_pattern = re.compile(r'Avg generation throughput: (\d+\.\d+) tokens/s')
        tokens_per_second_match = tokens_per_second_pattern.search(log_line)
        tokens_per_second = float(tokens_per_second_match.group(1)) if tokens_per_second_match else None
        data["tokens/s"] = tokens_per_second

    def extract_running_details(log_line, data):
        running_pattern = re.compile(r'Running: (\d+) reqs')
        running_match = running_pattern.search(log_line)
        num_running = int(running_match.group(1)) if running_match else None
        data["num_running"] = num_running

    def extract_pending_details(log_line, data):
        pending_pattern = re.compile(r'Pending: (\d+) reqs')
        pending_match = pending_pattern.search(log_line)
        num_pending = int(pending_match.group(1)) if pending_match else None
        data["num_pending"] = num_pending

    def handle_line(self, line):
        if self.update_pattern.search(line):
            data = {}
            self.extract_token_details(line, data)
            self.extract_running_details(line, data)
            self.extract_pending_details(line, data)
            self.send_model_update(data)

