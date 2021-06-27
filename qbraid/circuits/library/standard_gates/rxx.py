from ...gate import Gate

class RXX(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "RXX"