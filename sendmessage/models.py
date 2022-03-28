import json


class WebsocketResponse(object):
    def __init__(self, values: dict = None):
        values = values if values is not None else {}
        self.statusCode: int = values.get('status_code', None)
        self.message: object = values.get('message', None)

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
