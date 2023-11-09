class Backend():
    def __init__(self, *args, **kwargs):
        self.count = 0

def increment_handler(backend, request):
    backend.count += request.json["amount"]
    return "Incremented"

def value_handler(backend, request):
    return {"value" : backend.count}

flask_dict = {
    "POST" : {
        "increment" : increment_handler
    },
    "GET" : {
        "value" : value_handler
    }
}