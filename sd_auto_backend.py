from generic_backend import Backend
from server_metrics import IMGServerMetrics

MODEL_SERVER = '127.0.0.1:5000'

class SDAUTOBackend(Backend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = IMGServerMetrics(id=container_id, control_server_url=control_server_url, send_server_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.model_server_addr = MODEL_SERVER

    def txt2img(self, model_request):
        return super().generate(model_request, self.model_server_addr, "sdapi/v1/txt2img", lambda r: r.content, metrics=True)

    def generate_stream(self, model_request):
        pass


######################################### FLASK HANDLER METHODS ###############################################################

def txt2img_handler(backend, request):

    code, content, _ = backend.txt2img(request.json)

    if code == 200:
        return content
    else:
        print(f"txt2img failed with code {code}")
        abort(code)

flask_dict = {
    "POST" : {
        "sdapi/v1/txt2img" : txt2img_handler
    }
}