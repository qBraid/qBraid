from ...gate import ControlledGate, Gate

class Z(Gate):

    def __init__(self):
        pass

    def name(self):
        return "Z"

class ControlledZ(ControlledGate):

    def __init__(self):
        pass

    def name(self):
        return "CZ"