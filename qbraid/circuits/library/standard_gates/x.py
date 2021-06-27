from ...gate import ControlledGate, Gate

class X(Gate):

    def __init__(self):
        pass

    def name(self):
        return "X"

class ControlledX(ControlledGate):

    def __init__(self):
        pass

    def name(self):
        return "CX"