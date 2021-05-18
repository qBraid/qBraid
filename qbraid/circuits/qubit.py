from typing import Any, Sequence, Dict, Iterable, Union
from abc import ABC


from braket.circuits.qubit import Qubit as BraketQubit
from qiskit.circuit.quantumregister import Qubit as QiskitQubit
from cirq.ops.named_qubit import NamedQubit as CirqNamedQubit
from cirq.devices.line_qubit import LineQubit as CirqLineQubit

from qiskit.circuit.quantumregister import QuantumRegister as QiskitQuantumRegister

QubitInput = Union["BraketQubit", "CirqNamedQubit", "QiskitQubit", int, str]


class AbstractQubit(ABC):
    def __init__(self):

        self.qubit = None
        self.index = None
        self._outputs = {}

    def transpile(self, package: str):

        """If transpile object not already created, create it an dreturn the
        object, which is stored for future used."""

        if not package in self._outputs.keys():
            self._create_output(package)
        return self._outputs[package]

    def _create_output(self, package: str):

        """Create the transpiledobject for a specific package"""

        if package == "qiskit":
            print("ERROR: Qiskit output object must be created from circuit object.")
        elif package == "braket":
            self._create_braket()
        elif package == "cirq":
            self._create_cirq()
        else:
            print("package not yet handled")

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


# =============================================================================
# class Qubit():
#
#     """
#     Qubit Class: hold qubit objects
#
#     Args:
#         qubit: input object, acceptable objects include:
#             Braket, qiskit, cirq
#     """
#
#     def __init__(self,
#                  qubit: QubitInput = None,
#                  identifier: Union[int,str] = None):
#
#         self.qubit = qubit
#         self.id = identifier
#
#         if isinstance(qubit,QiskitQubit):
#             self.index = qubit.index
#         elif isinstance(qubit,CirqLineQubit):
#             self.index = qubit.x
#         elif isinstance(qubit,BraketQubit):
#             self.index = int(qubit)
#
#         self.outputs = {}
#
#     def _create_cirq_object(self):
#
#         self.outputs['cirq'] = CirqLineQubit(self.index)
#
#     def _create_qiskit_object(self,register: QiskitQuantumRegister):
#
#         self.outputs['qiskit'] = QiskitQubit(register, self.index)
#
#     def _create_braket_object(self):
#
#         self.outputs['braket'] = BraketQubit(self.index)
#
#     def _to_cirq(self):
#
#         if 'cirq' not in self.outputs.keys() or not self.outputs['cirq']:
#             self._create_cirq_object()
#
#         return self.outputs['cirq']
#
#     def _to_qiskit(self):
#
#         try:
#             return self.outputs['qiskit']
#         except:
#             print("qiskit output not initialized in qubit {}".format(self.id))
#
#     def _to_braket(self):
#
#         if 'braket' not in self.outputs.keys() or not self.outputs['braket']:
#             self._create_braket_object()
#
#         return self.outputs['braket']
#
#     def output(self, package: str):
#
#         if package == 'qiskit':
#             return self._to_qiskit()
#         elif package == 'cirq':
#             return self._to_cirq()
#         elif package == 'braket':
#             return self._to_braket()
# =============================================================================
