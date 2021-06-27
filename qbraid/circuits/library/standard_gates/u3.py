from ...gate import Gate

class U3(Gate):

    def __init__(self, theta, phi, lam):
        self.theta=theta
        self.phi=phi
        self.lam=lam

    def name(self):
        return "U3"