from generic_backend import Backend
from server_metrics import IMGServerMetrics

MODEL_SERVER = '127.0.0.1:5001'

class SDAUTOBackend(Backend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = IMGServerMetrics(id=container_id, control_server_url=control_server_url, send_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.model_server_addr = MODEL_SERVER

    def txt2img(self, model_request):
        return super().generate(model_request, self.model_server_addr, "sdapi/v1/txt2img", lambda r: r.text, metrics=True)

    def generate_stream(self, model_request):
        pass


######################################### FLASK HANDLER METHODS ###############################################################

def txt2img_handler(backend, request):
    return backend.txt2img(request)

flask_dict = {"sdapi/v1/txt2img" : txt2img_handler}