from ...gate import Gate

class RZX(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "RZX"