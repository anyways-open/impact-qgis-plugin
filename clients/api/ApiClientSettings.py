from ...settings import API

class ApiClientSettings(object):
    def __init__(self, url=None):
        self.url = API if url is None else url
        self.timeout = 2