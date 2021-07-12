from abc import abstractmethod
from qbraid.exceptions import PackageError
from .outputs import circuit_outputs
from .wrapper import QbraidWrapper


class CircuitWrapper(QbraidWrapper):
    def __init__(self):
        self.instructions = []
        self.params = []
        self.circuit = None

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        pass

    def transpile(self, package, **kwargs):

        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self)
        else:
            raise PackageError(f"{package} is not a supported package.")
