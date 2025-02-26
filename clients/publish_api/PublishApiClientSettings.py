from ...settings import PUBLISH_API

class PublishApiClientSettings(object):
    def __init__(self, url=None):
        self.url = PUBLISH_API if url is None else url