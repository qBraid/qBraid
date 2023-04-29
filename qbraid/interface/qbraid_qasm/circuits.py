"""
Module containing qasm programs used for testing

"""
import os

QASMType = str
current_dir = os.path.dirname(os.path.abspath(__file__))

def qasm_bell() -> QASMType:
    """Returns QASM2 bell circuit"""
    return open(os.path.join(current_dir, "bell.qasm"), "r").read()

def qasm_shared15():
    """Returns QASM2 for qBraid `TestSharedGates`."""
    return open(os.path.join(current_dir, "shared_15.qasm") ,"r").read()
