import itertools
import numpy as np

from cirq import Circuit as CirqCircuit

import braket.ir.jaqcd as ir
from braket.circuits import Circuit as BKCircuit, Gate, Instruction, circuit
from braket.circuits.unitary_calculation import calculate_unitary
from braket.circuits.qubit_set import QubitSet

from qbraid.transpiler2.utils import _unitary_cirq


def _unitary_braket(circuit: BKCircuit) -> np.ndarray:
    """Calculate unitary of a braket circuit."""
    return calculate_unitary(circuit.qubit_count, circuit.instructions)


def _equal_unitaries(
    braket_circuit: BKCircuit, cirq_circuit: CirqCircuit
) -> bool:
    """Returns True if Braket circuit unitary and Cirq circuit
    unitary are equivalent."""
    braket_unitary = _unitary_braket(braket_circuit)
    cirq_unitary = _unitary_cirq(cirq_circuit)
    return np.allclose(braket_unitary, cirq_unitary)


class C(Gate):
    """Controlled gate
    Args:
        sub_gate (Gate): Quantum Gate.
        targets (QubitSet): Target qubits.
    """

    def __init__(self, sub_gate: Gate, targets: QubitSet):
        self.sub_gate = sub_gate
        qubit_count = len(targets)
        sub_qubit_count = sub_gate.qubit_count
        self._num_controls = qubit_count - sub_qubit_count
        self._controls = targets[: self._num_controls]
        ascii_symbols = ["C"] * self._num_controls + list(
            self.sub_gate.ascii_symbols
        )

        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    def _extend_matrix(self, sub_matrix: np.ndarray) -> np.ndarray:
        qid_shape = (2,) * self.qubit_count
        control_values = ((1,),) * self._num_controls
        sub_n = len(qid_shape) - self._num_controls
        tensor = np.eye(
            np.prod(qid_shape, dtype=np.int64).item(), dtype=sub_matrix.dtype
        )
        tensor.shape = qid_shape * 2
        sub_tensor = sub_matrix.reshape(qid_shape[self._num_controls :] * 2)
        for control_vals in itertools.product(*control_values):
            active = (*(v for v in control_vals), *(slice(None),) * sub_n) * 2
            tensor[active] = sub_tensor
        return tensor.reshape((np.prod(qid_shape, dtype=np.int64).item(),) * 2)

    def to_matrix(self):
        sub_matrix = self.sub_gate.to_matrix()
        return self._extend_matrix(sub_matrix)

    def to_ir(self, target: QubitSet):
        return ir.Unitary.construct(
            targets=[qubit for qubit in target],
            matrix=C._transform_matrix_to_ir(self.to_matrix()),
        )

    def __eq__(self, other):
        if isinstance(other, C):
            return self.matrix_equivalence(other)
        return NotImplemented

    @staticmethod
    def _transform_matrix_to_ir(matrix: np.ndarray):
        return [
            [[element.real, element.imag] for element in row]
            for row in matrix.tolist()
        ]

    @staticmethod
    @circuit.subroutine(register=True)
    def c(targets: QubitSet, sub_gate: Gate) -> Instruction:
        """Registers this function into the circuit class.
        Args:
            targets (QubitSet): Target qubits.
            sub_gate (Gate): Quantum Gate.
        Returns:
            Instruction: Controlled Gate Instruction.
        """
        return Instruction(C(sub_gate, targets), target=targets)


Gate.register_gate(C)
