import abc
from abc import ABC
from typing import Union

from qiskit.circuit import Parameter as QiskitParameter
from sympy import Symbol as CirqParameter

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

    @abc.abstractmethod
    def transpile(self, package: str):
        pass


# class CirqParameterWrapper(AbstractParameterWrapper):
#     """qBraid wrapper of cirq paramter object."""

#     def __init__(self, parameter: CirqParameter):

#         super().__init__()
#         self.name = parameter.name
#         self.parameter = parameter

#     def transpile(self, package: str):

#         if package == "cirq":
#             return self.parameter
#         elif package == "qiskit":
#             if "qiskit" not in self._outputs.keys():
#                 self._create_qiskit()
#             return self._outputs["qiskit"]
#         else:
#             raise PackageError(package)


# class QiskitParameterWrapper(AbstractParameterWrapper):
#     """qbraid wrapper of qiskit parameter object."""

#     def __init__(self, parameter: QiskitParameter):

#         super().__init__()
#         self.name = parameter.name
#         self.parameter = parameter

#     def transpile(self, package: str):

#         if package == "cirq":
#             if "cirq" not in self._outputs.keys():
#                 self._create_cirq()
#             return self._outputs["cirq"]
#         elif package == "qiskit":
#             return self.parameter
#         elif package == "braket":
#             raise PackageError(package, "for transpiling parameterized circuits")
#         else:
#             raise PackageError(package)
