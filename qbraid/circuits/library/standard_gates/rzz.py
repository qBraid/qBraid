from ...gate import Gate

class RZZ(Gate):

    def __init__(self, phi):
        self.phi=phi

    def name(self):
        return "RZZ"