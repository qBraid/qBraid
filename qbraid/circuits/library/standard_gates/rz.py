from ...gate import Gate

class RZ(Gate):

    def __init__(self, phi):
        self.phi=phi

    def name(self):
        return "RZ"