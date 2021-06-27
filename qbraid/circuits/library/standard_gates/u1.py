from ...gate import Gate

class U1(Gate):

    def __init__(self, theta):
        self.theta=theta

    def name(self):
        return "U1"