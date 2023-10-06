import secrets
from abc import ABC, abstractmethod
from auth import fetch_public_key, verify_signature
import sys
import json

NUM_AUTH_TOKENS = 1000
MSG_HISTORY_LEN = 100

class Backend(ABC):
    def __init__(self, container_id, control_server_url, master_token):
        self.curr_auth_tokens = set()
        self.num_auth_tokens = NUM_AUTH_TOKENS
        self.container_id = container_id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.reqnum = 0
        self.msg_history = []

        self.public_key = fetch_public_key()

    def get_auth_tokens(self):
        new_token_batch = []
        for _ in range(self.num_auth_tokens):
            token = secrets.token_hex(32)
            new_token_batch.append(token)
        self.curr_auth_tokens |= set(new_token_batch)

        return new_token_batch

    def check_master_token(self, token):
        return token == self.master_token

    def check_auth_token(self, token):
        if token in self.curr_auth_tokens:
            self.curr_auth_tokens.remove(token)
            return True
        elif token == self.master_token:
            return True
        else:
            return False

    def format_request(self, request):
        if "signature" in request.keys():
            original_dict = {"cost" : request["cost"], "endpoint" : request["endpoint"], "reqnum" : request["reqnum"], "url" : request["url"]}
            message = json.dumps(original_dict, indent=4)
            auth_dict = {"signature" : request["signature"], "message": message, "reqnum" : request["reqnum"]}
        else:
            auth_dict = None
        model_dict = {"inputs" : request["inputs"], "parameters" : request["parameters"]}
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

    @abstractmethod
    def generate(self, inputs, parameters):
        pass

    @abstractmethod
    def generate_stream(self, inputs, parameters):
        pass

