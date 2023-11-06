from flask import abort

from backend import GenericBackend
from sdauto.metrics import Metrics

MODEL_SERVER = '127.0.0.1:5000'

class Backend(GenericBackend):
    def __init__(self, container_id, control_server_url, master_token, send_data):
        metrics = Metrics(id=container_id, control_server_url=control_server_url, send_server_data=send_data)
        super().__init__(master_token=master_token, metrics=metrics)
        self.model_server_addr = MODEL_SERVER

    def txt2img(self, model_request):
        return super().generate(model_request, self.model_server_addr, "sdapi/v1/txt2img", lambda r: r.content, metrics=True)

######################################### FLASK HANDLER METHODS ###############################################################

def txt2img_handler(backend, request):

    auth_dict, model_dict = backend.format_request(request.json)
    if auth_dict:
        if not backend.check_signature(**auth_dict):
            abort(401)

    code, content, _ = backend.txt2img(model_dict)

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