from abc import abstractmethod, ABC

from .utils import circuit_outputs, supported_packages
from qbraid.exceptions import PackageError


class CircuitWrapper(ABC):
    def __init__(self):

        self.instructions = []
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

    def transpile(self, package, **kwargs):

        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self, **kwargs)
        else:
            raise PackageError(f"{package} is not a supported package.")

