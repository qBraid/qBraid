from typing import Union

from qiskit.circuit import Parameter as QiskitParameter
from sympy import Symbol as CirqParameter

from .transpiler import QbraidTranspiler

ParameterInput = Union[float, int, str]


class ParamID:
    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name


class ParameterWrapper(QbraidTranspiler):
    """Wrap a 'parameter' for parametrized circuits"""

    def __init__(self):
        self.name = None
        self.parameter = None

    def _create_cirq(self):
        return CirqParameter(self.name)

    def _create_qiskit(self):
        return QiskitParameter(self.name)

    def transpile(self, package, *args, **kwargs):
        return NotImplementedError
