from ...settings import EDIT_API

class EditApiClientSettings(object):
    def __init__(self, url=None):
        self.url = EDIT_API if url is None else url