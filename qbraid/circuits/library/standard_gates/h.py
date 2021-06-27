from ...gate import ControlledGate, Gate

class H(Gate):
    
    def __init__(self):
        pass

    def name(self):
        return "H"

class ControlledH(ControlledGate):

    def __init__(self):
        pass

    def name(self):
        return "CH"