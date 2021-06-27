from ...gate import Gate

class RY(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "RY"