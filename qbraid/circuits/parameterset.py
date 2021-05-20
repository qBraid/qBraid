from abc import ABC
from typing import Iterable

from qiskit.circuit.parameter import Parameter as QiskitParameter
from sympy import Symbol

from .parameter import QiskitParameterWrapper, CirqParameterWrapper, AbstractParameterWrapper


class AbstractParameterSet(ABC):
    def __init__(self):

        self.parameters = []
        self._outputs = {}

    def get_parameter(self, search_target_parameter):

        """Same as get_qubit but for parameters."""

        for param in self.parameters:
            if param.parameter == search_target_parameter:
                return param

    def get_parameters(self, search_target_parameters: Iterable):
        pass

    def _create_qiskit(self):
        self._outputs["qiskit"] = [p.transpile["qiskit"] for p in self.parameters]

    def _create_braket(self):
        pass

    def _create_cirq(self):
        self._outputs["cirq"] = [p.transpile["cirq"] for p in self.parameters]

    def transpile(self, package: str):

        """Create transpiled object if it has not been created altready. Return"""

        if package not in self._outputs.keys():
            self._create_output(package)
        return self._outputs[package]

    def _create_output(self, package: str):

        if package == "qiskit":
            self._create_qiskit()
        elif package == "cirq":
            self._create_cirq()
        elif package == "braket":
            raise ValueError("Braket not yet supported for parametrized circuits.")
        else:
            raise ValueError("Package not supported")


class QiskitParameterSet(AbstractParameterSet):
    def __init__(self, parameters: Iterable[QiskitParameterWrapper]):

        super().__init__()
        self.parameters = [QiskitParameterWrapper(p) for p in parameters]

    def get_parameters(self, search_target_parameters: Iterable):

        output = []
        for param in search_target_parameters:
            if isinstance(param, QiskitParameter):
                output.append(self.get_parameter(param))
            else:
                output.append(param)

        for p in output:
            assert isinstance(p, (float, int, AbstractParameterWrapper))

        return output


class CirqParameterSet(AbstractParameterSet):
    def __init__(self, parameters: Iterable[CirqParameterWrapper]):

        super().__init__()
        self.parameters = [CirqParameterWrapper(p) for p in parameters]

    def get_parameters(self, search_target_parameters: Iterable):

        output = []
        for param in search_target_parameters:
            if isinstance(param, Symbol):
                output.append(self.get_parameter(param))
            else:
                output.append(param)

        for p in output:
            assert isinstance(p, (float, int, AbstractParameterWrapper))

        return output
