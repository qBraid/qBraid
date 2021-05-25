from typing import Union
from qiskit.circuit import Parameter as QiskitParameter
from sympy import Symbol
from qbraid.exceptions import PackageError

ParameterInput = Union[float, int, str]


class AbstractParameterWrapper:
    """Wrap a 'parameter' for parametrized circuits"""

    def __init__(self):
        self.name = None
        self.parameter = None

        self._outputs = {}

    def _create_cirq(self):
        self._outputs["cirq"] = Symbol(self.name)

    def _create_qiskit(self):
        self._outputs["qiskit"] = QiskitParameter(self.name)

    def transpile(self, package: str):
        raise NotImplementedError


class CirqParameterWrapper(AbstractParameterWrapper):
    """qBraid wrapper of cirq paramter object."""

    def __init__(self, parameter: Symbol):

        super().__init__()
        self.name = parameter.name
        self.parameter = parameter

    def transpile(self, package: str):

        if package == "cirq":
            return self.parameter
        elif package == "qiskit":
            if "qiskit" not in self._outputs.keys():
                self._create_qiskit()
            return self._outputs["qiskit"]
        else:
            raise PackageError(package)


class QiskitParameterWrapper(AbstractParameterWrapper):
    """qbraid wrapper of qiskit parameter object."""

    def __init__(self, parameter: QiskitParameter):

        super().__init__()
        self.name = parameter.name
        self.parameter = parameter

    def transpile(self, package: str):

        if package == "qiskit":
            return self.parameter
        elif package == "cirq":
            if "cirq" not in self._outputs.keys():
                self._create_cirq()
            return self._outputs["cirq"]
        else:
            raise PackageError(package)
