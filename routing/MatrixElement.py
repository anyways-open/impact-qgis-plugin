class MatrixElement(object):
    def __init__(self, origin: int, destination: int, count: int, profile: str = None):
        self.origin = origin
        self.destination = destination
        self.count = count
        self.profile = profile
