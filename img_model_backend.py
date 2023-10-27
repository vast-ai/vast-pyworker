from abc import abstractmethod

from abstract_backend import Backend
from server_metrics import IMGServerMetrics

class IMGBackend(Backend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        super().__init__(container_id=container_id, control_server_url=control_server_url, master_token=master_token)
        self.metrics = IMGServerMetrics(id=container_id, control_server_url=control_server_url, master_token=master_token, send_data=send_data)

    @abstractmethod
    def generate(self, model_request):
        pass

    @abstractmethod
    def generate_stream(self, model_request):
        pass