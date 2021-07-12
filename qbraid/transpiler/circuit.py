from abc import abstractmethod
from typing import Union

from braket.circuits.circuit import Circuit as BraketCircuit
from cirq.circuits import Circuit as CirqCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit

from qbraid.exceptions import PackageError
from .outputs import circuit_outputs
from .wrapper import QbraidWrapper

SupportedCircuit = Union[BraketCircuit, CirqCircuit, QiskitCircuit]


class CircuitWrapper(QbraidWrapper):
    def __init__(self):
        self.instructions = []
        self.params = []
        self.circuit = None

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        pass

    def transpile(self, package: str) -> SupportedCircuit:

        if package == self.package:
            return self.circuit
        elif package in self.supported_packages:
            return circuit_outputs[package](self)
        else:
            raise PackageError(
                f"Transpiling a circuit from {self.package} to {package} is not supported."
            )
