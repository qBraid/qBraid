from ...gate import Gate

class U2(Gate):

    def __init__(self, phi, lam):
        self.phi=phi
        self.lam=lam

    def name(self):
        return "U2"