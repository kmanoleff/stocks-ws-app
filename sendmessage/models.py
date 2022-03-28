import json


class WebsocketResponse(object):
    def __init__(self, status_code, report_data, message):
        self.statusCode = status_code
        self.reportData = report_data
        self.message = message

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class ReportData(object):
    def __init__(self, avg_stock, min_stock, max_stock, min_volume, max_volume):
        self.avgStock = avg_stock
        self.minStock = min_stock
        self.maxStock = max_stock
        self.minVolume = min_volume
        self.maxVolume = max_volume

    def json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
