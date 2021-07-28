from abc import abstractmethod

from .transpiler import QbraidTranspiler
from .exceptions import TranspilerError
from ._utils import circuit_outputs, supported_packages


class CircuitWrapper(QbraidTranspiler):
    def __init__(self):

        self.instructions = []
        self.moments = []
        self.params = []
        self.circuit = None
        self._package = None

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        pass

    @property
    def package(self):
        return self._package

    @property
    def supported_packages(self):
        return supported_packages[self.package]

    def transpile(self, package, *args, **kwargs):
        """

        Args:
            package:

        Returns:

        """
        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self, *args, **kwargs)
        else:
            raise TranspilerError(f"{package} is not a supported package.")
