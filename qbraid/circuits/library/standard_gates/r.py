from ...gate import Gate

class R(Gate):

    def __init__(self, theta, phi):
        self.theta=theta
        self.phi=phi

    def name(self):
        return "R"