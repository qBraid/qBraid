from abc import abstractmethod, ABC

from .utils import circuit_outputs
from qbraid.exceptions import PackageError


class CircuitWrapper(ABC):
    def __init__(self):
        self.instructions = []
        self.params = []
        self.circuit = None

    @property
    @abstractmethod
    def package(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_packages(self) -> list:
        pass

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        pass

    def transpile(self, package: str, **kwargs):

        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self)
        else:
            raise PackageError(f"{package} is not a supported package.")

