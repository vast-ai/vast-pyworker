from abc import abstractmethod


from abstract_backend import Backend
from server_metrics import LLMServerMetrics

class LLMBackend(Backend):
    def __init__(self, container_id, control_server_url, master_token):
        super().__init__(container_id=container_id, control_server_url=control_server_url, master_token=master_token)
        self.metrics = LLMServerMetrics(id=container_id, control_server_url=control_server_url, master_token=master_token)

    @abstractmethod
    def generate(self, inputs, parameters):
        pass

    @abstractmethod
    def generate_streaming(self, inputs, parameters):
        pass
    


        