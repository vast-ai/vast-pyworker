import secrets
from abc import ABC, abstractmethod
from auth import format_public_key, load_public_key, verify_signature

NUM_AUTH_TOKENS = 1000
MSG_HISTORY_LEN = 10

class Backend(ABC):
    def __init__(self, container_id, control_server_url, master_token):
        self.curr_auth_tokens = set()
        self.num_auth_tokens = NUM_AUTH_TOKENS
        self.container_id = container_id
        self.control_server_url = control_server_url
        self.master_token = master_token
        self.req_num = 0
        self.msg_history = []

        # self.crypto = format_public_key()
        self.crypto = True
        if self.crypto:
            self.public_key = load_public_key()

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

    def check_signature(self, req_num, message, signature):
        print(f"[checking signature] req_num: {req_num} message: {message}, signature: {signature}")
        if not self.crypto:
            return True
        if req_num < (self.req_num - MSG_HISTORY_LEN):
            return False
        elif message in self.msg_history:
            return False
        elif verify_signature(self.public_key, message, signature):
            print("[checking signature] SUCCESS")
            self.req_num = req_num
            self.msg_history.append(message)
            if len(self.msg_history) > MSG_HISTORY_LEN:
                self.msg_history = self.msg_history[len(self.msg_history) - MSG_HISTORY_LEN: ]
            return True
        else:
            print("[checking signature] FAILED")
            return False

    @abstractmethod
    def generate(self, inputs, parameters):
        pass

    @abstractmethod
    def generate_stream(self, inputs, parameters):
        pass

