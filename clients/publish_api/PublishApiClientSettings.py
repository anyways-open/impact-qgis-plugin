from ...settings import API

class PublishApiClientSettings(object):
    def __init__(self, url=None):
        self.url = API if url is None else url
        self.timeout = 6000
