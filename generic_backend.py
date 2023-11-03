from auth import fetch_public_key, verify_signature
import json
import time
import requests
 
MSG_HISTORY_LEN = 100

class Backend():
    def __init__(self, master_token, metrics):
        self.master_token = master_token
        self.metrics = metrics
        
        self.reqnum = 0
        self.msg_history = []

        self.public_key = fetch_public_key()

    def check_master_token(self, token):
        return token == self.master_token

    def format_request(self, request):
        model_dict = {}
        model_dict.update(request)
        auth_names = ["signature", "endpoint", "reqnum", "url", "message"]
        has_auth = True
        for key in auth_names:
            if key not in request.keys():
                has_auth = False
            else:
                del model_dict[key]

        if has_auth:
            original_dict = {"cost" : request["cost"], "endpoint" : request["endpoint"], "reqnum" : request["reqnum"], "url" : request["url"]}
            message = json.dumps(original_dict, indent=4)
            auth_dict = {"signature" : request["signature"], "message": message, "reqnum" : request["reqnum"]}
        else:
            auth_dict = None
        
        return auth_dict, model_dict

    def check_signature(self, reqnum, message, signature):
        if reqnum < (self.reqnum - MSG_HISTORY_LEN):
            return False
        elif message in self.msg_history:
            return False
        elif verify_signature(self.public_key, message, signature):
            self.reqnum = max(reqnum, self.reqnum)
            self.msg_history.append(message)
            if len(self.msg_history) > MSG_HISTORY_LEN:
                self.msg_history = self.msg_history[len(self.msg_history) - MSG_HISTORY_LEN: ]
            return True
        else:
            return False

    def generate(self, model_request, model_server_addr, endpoint, response_func, metrics=False):
        if metrics:
            self.metrics.start_req(model_request)
        try:
            t1 = time.time()
            response = requests.post(f"http://{model_server_addr}/{endpoint}", json=model_request)
            t2 = time.time()
            
            if response.status_code == 200:
                if metrics:
                    model_request["time_elapsed"] = t2 - t1
                    self.metrics.finish_req(model_request)

                return 200, response_func(response), t2 - t1
            else:
                ret_code = response.status_code
        
        except requests.exceptions.RequestException as e:
            ret_code = 500
            print(f"[backend] Request error: {e}")

        if metrics:
            self.metrics.error_req(model_request)
        
        return ret_code, None, None

    def get(self, request, model_server_addr, endpoint, response_func):
        try:
            response = requests.get(f"http://{model_server_addr}/{endpoint}", json=request)
            if response.status_code == 200:
                return 200, response_func(response)
            else:
                ret_code = response.status_code

        except requests.exceptions.RequestException as e:
            ret_code = 500
            print(f"[backend] Request error: {e}")

        return ret_code, None


