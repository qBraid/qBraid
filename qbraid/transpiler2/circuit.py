import abc
from abc import ABC
from .qbraid.gate import QbraidGateWrapper
from .qbraid.instruction import QbraidInstructionWrapper
from typing import Union

from braket.circuits.circuit import Circuit as BraketCircuit
from cirq.circuits import Circuit as CirqCircuit
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.circuit.classicalregister import (
    ClassicalRegister as QiskitClassicalRegister,
)

SupportedCircuit = Union[BraketCircuit, CirqCircuit, QiskitCircuit]


class AbstractCircuitWrapper(ABC):
    def __init__(self):
        self.instructions = []

    @property
    @abc.abstractmethod
    def num_qubits(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def num_clbits(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def supported_packages(self) -> list:
        pass

    @abc.abstractmethod
    def transpile(self, package: str) -> SupportedCircuit:
        pass

