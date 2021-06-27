from ...gate import Gate

class RX(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "RX"