from abc import ABC
from typing import Iterable

# from braket.circuits.qubit_set import QubitSet as BraketQubitSet
from braket.circuits.qubit import Qubit as BraketQubit
from .qubit import BraketQubitWrapper

from cirq.devices.line_qubit import LineQubit as CirqLineQubit
from .qubit import CirqQubitWrapper

from qiskit.circuit.quantumregister import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.quantumregister import Qubit as QiskitQubit
from .qubit import QiskitQubitWrapper


class AbstractQubitSet(ABC):
    """Not a qubit set in the sense of qiskit 'QuantumRegister', but rather a
    list of qbraid-wrapped qubit objects."""

    def __init__(self):

        self.qubits = []
        self._outputs = {}

    def get_qubit(self, search_target_qubit):
        """Find the qbraid qubit object that has wrapped the object of whatever package.
        Used by instruction object to find the qubit relavent to that instruction.
        This is somewhat inefficient, and we may want to change this over time."""

        for qb in self.qubits:
            if qb.qubit == search_target_qubit:
                return qb

    def get_qubits(self, search_target_qubits: Iterable):
        """Run get_qubit on a list of package-level qubit objects"""

        return [self.get_qubit(target) for target in search_target_qubits]

    def _transpile_qubits(self, package: str):
        pass

    def _create_braket(self):
        self._outputs["braket"] = [qb.transpile("braket") for qb in self.qubits]

    def _create_cirq(self):
        self._outputs["cirq"] = [qb.transpile("cirq") for qb in self.qubits]

    def _create_qiskit(self):

        qreg = QiskitQuantumRegister(len(self.qubits))
        for index, qubit in enumerate(self.qubits):
            qubit._create_qiskit(qreg, index)

        self._outputs["qiskit"] = qreg

    def transpile(self, package: str):
        """Should check if the transpiled object has already been created.
        If not, create it. Then return that object."""

        if package == "qiskit":
            self._create_qiskit()

        return self._outputs["qiskit"]


class BraketQubitSet(AbstractQubitSet):
    def __init__(self, qubits: Iterable[BraketQubit]):
        super().__init__()
        self.qubits = [BraketQubitWrapper(qb) for qb in qubits]


class CirqQubitSet(AbstractQubitSet):
    def __init__(self, qubits: Iterable[CirqLineQubit]):
        super().__init__()
        self.qubits = [CirqQubitWrapper(qb) for qb in qubits]


class QiskitQubitSet(AbstractQubitSet):
    def __init__(self, qubits: Iterable[QiskitQubit]):
        super().__init__()
        self.qubits = [QiskitQubitWrapper(qb) for qb in qubits]
