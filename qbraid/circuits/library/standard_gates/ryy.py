from ...gate import Gate

class RYY(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "RYY"