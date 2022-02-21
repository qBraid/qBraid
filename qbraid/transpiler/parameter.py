"""Paramater Module"""

from typing import Union

from qiskit.circuit import Parameter as QiskitParameter
from sympy import Symbol as CirqParameter

from qbraid.transpiler.transpiler import QbraidTranspiler

ParameterInput = Union[float, int, str]


class ParamID:
    """An itermediate representation for storing abstract parameters during the
    transpilation process. This class is needed, as opposed to a serial number,
    in order to distinguish abstract parameters from numbers.

    Attributes:
        index (integer): a serial number given to arbitrarily to each parameter
        name (str): name of the parameter as string
    """

    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name
