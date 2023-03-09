"""
Module containing pyQuil programs used for testing

"""
from pyquil import Program
from pyquil.gates import CNOT, H


def pyquil_bell() -> Program:
    """Returns pyQuil bell circuit"""
    program = Program()
    program += H(1)
    program += CNOT(1, 0)
    return program
