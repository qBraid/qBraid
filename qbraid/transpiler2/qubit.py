from abc import ABC
from typing import Union

from braket.circuits.qubit import Qubit as BraketQubit
from cirq.devices.line_qubit import LineQubit as CirqLineQubit
from qiskit.circuit.quantumregister import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.quantumregister import Qubit as QiskitQubit

from qbraid.exceptions import PackageError

QubitInput = Union["BraketQubit", "CirqNamedQubit", "QiskitQubit", int, str]


class AbstractQubit(ABC):
    def __init__(self):

        self.qubit = None
        self.index = None
        self._outputs = {}

    def transpile(self, package: str):

        """If transpile object not already created, create it and return the
        object, which is stored for future used."""

        if package not in self._outputs.keys():
            self._create_output(package)
        return self._outputs[package]

    def _create_output(self, package: str):

        """Create the transpiled object for a specific package"""

        if package == "braket":
            self._create_braket()
        elif package == "cirq":
            self._create_cirq()
        elif package == "qiskit":
            raise ValueError("Qiskit output object must be created from circuit object")
        else:
            raise PackageError(package)

    def _create_qiskit(self, register: QiskitQuantumRegister, index: int):

        self._outputs["qiskit"] = QiskitQubit(register, index)

    def _create_cirq(self):

        self._outputs["cirq"] = CirqLineQubit(self.index)

    def _create_braket(self):

        self._outputs["braket"] = BraketQubit(self.index)


class QiskitQubitWrapper(AbstractQubit):
    def __init__(self, qubit: QiskitQubit):
        super().__init__()
        self.qubit = qubit
        self.index = qubit.index


class CirqQubitWrapper(AbstractQubit):
    def __init__(self, qubit: CirqLineQubit):
        super().__init__()
        self.qubit = qubit
        self.index = qubit.x


class BraketQubitWrapper(AbstractQubit):
    def __init__(self, qubit: BraketQubit):
        super().__init__()
        self.qubit = qubit
        self.index = int(qubit)
