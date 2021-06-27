from ...gate import ControlledGate, Gate

class Y(Gate):

    def __init__(self):
        pass

    def name(self):
        return "Y"

class ControlledY(ControlledGate):

    def __init__(self):
        pass

    def name(self):
        return "CY"