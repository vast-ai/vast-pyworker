import secrets
from abc import ABC, abstractmethod

NUM_AUTH_TOKENS = 1000

class Backend(ABC):
    def __init__(self, container_id, control_server_url, master_token):
        self.curr_auth_tokens = set()
        self.num_auth_tokens = NUM_AUTH_TOKENS
        self.container_id = container_id
        self.control_server_url = control_server_url
        self.master_token = master_token

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
        
    @abstractmethod
    def generate(self, inputs, parameters):
        pass

    @abstractmethod
    def generate_streaming(self, inputs, parameters):
        pass

