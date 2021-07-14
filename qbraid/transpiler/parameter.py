from abc import ABC, abstractmethod
from qiskit.circuit import Parameter as QiskitParameter
from sympy import Symbol as CirqParameter
from typing import Union

ParameterInput = Union[float, int, str]


class ParamID:
    def __init__(self, index: int, name: str):
        self.index = index
        self.name = name


class ParameterWrapper(ABC):
    """Wrap a 'parameter' for parametrized circuits"""

    def __init__(self):
        self.name = None
        self.parameter = None
        self._outputs = {}

    def _create_cirq(self):
        self._outputs["cirq"] = CirqParameter(self.name)

    def _create_qiskit(self):
        self._outputs["qiskit"] = QiskitParameter(self.name)

    @abstractmethod
    def transpile(self, package: str):
        pass
