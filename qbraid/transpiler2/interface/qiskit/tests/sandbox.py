from cirq.circuits import qasm_output
import numpy as np

from cirq.circuits.qasm_output import QasmUGate
from cirq import Circuit, LineQubit, ops, protocols, unitary, linalg
from cirq.linalg.decompositions import (
    kak_decomposition,
    deconstruct_single_qubit_matrix_into_angles,
    _phase_matrix,
)

from qiskit.circuit.library.standard_gates import iSwapGate
from qiskit import QuantumCircuit as QiskitCircuit
from cirq import Circuit as CirqCircuit
import cirq

from qbraid.transpiler2.interface.cirq_qasm_gates import ZPowGate
from qbraid.transpiler2.utils import _unitary_cirq, _convert_to_line_qubits
from qbraid.transpiler2.interface.qiskit.qiskit_utils import (
    _equal_unitaries,
    _unitary_qiskit,
)
from qbraid.transpiler2.interface import convert_to_cirq, convert_from_cirq
from qbraid.transpiler2.interface.qiskit.qiskit_utils import (
    _unitary_cirq,
    _unitary_qiskit,
    _equal_unitaries,
)
from qbraid.transpiler2.interface.qiskit.conversions import (
    from_qiskit,
    to_qiskit,
    from_qasm,
)
from qbraid.transpiler2.interface.qasm_output import QasmOutput
from qbraid.transpiler2.interface.to_qasm import _to_qasm_output, circuit_to_qasm

from qiskit import QuantumCircuit
from qiskit.extensions.unitary import UnitaryGate


def qiskit_shared_gates_circuit():
    """Returns qiskit `QuantumCircuit` for qBraid `TestSharedGates`."""

    circuit = QiskitCircuit(4)

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.sdg(1)
    circuit.t(2)
    circuit.tdg(3)
    circuit.rx(np.pi / 4, 0)
    circuit.ry(np.pi / 2, 1)
    circuit.rz(3 * np.pi / 4, 2)
    circuit.p(np.pi / 8, 3)
    circuit.sx(0)
    # circuit.sxdg(1)
    # circuit.iswap(2, 3)
    # circuit.swap([0, 1], [2, 3])
    circuit.cx(0, 1)
    # circuit.cp(np.pi / 4, 2, 3)

    # unitary = _unitary_qiskit(circuit)
    # cirq_circuit = convert_to_cirq(circuit)

    return circuit


def cirq_shared_gates_circuit():
    """Returns cirq `Circuit` for qBraid `TestSharedGates`
    rev_qubits=True reverses ordering of qubits."""

    circuit = CirqCircuit()
    q3, q2, q1, q0 = [cirq.LineQubit(i) for i in range(4)]
    mapping = {q3: 0, q2: 1, q1: 2, q0: 3}

    cirq_shared_gates = [
        cirq.H(q0),
        cirq.H(q1),
        cirq.H(q2),
        cirq.H(q3),
        cirq.X(q0),
        cirq.X(q1),
        cirq.Y(q2),
        cirq.Z(q3),
        cirq.S(q0),
        cirq.ZPowGate(exponent=-0.5)(q1),
        cirq.T(q2),
        cirq.ZPowGate(exponent=-0.25)(q3),
        cirq.rx(rads=np.pi / 4)(q0),
        cirq.ry(rads=np.pi / 2)(q1),
        cirq.rz(rads=3 * np.pi / 4)(q2),
        cirq.ZPowGate(exponent=1 / 8)(q3),
        cirq.XPowGate(exponent=0.5)(q0),
        # cirq.XPowGate(exponent=-0.5)(q1),
        # cirq.ISWAP(q2, q3),
        # cirq.SWAP(q0, q2),
        # cirq.SWAP(q1, q3),
        cirq.CNOT(q0, q1),
        # cirq.CZPowGate(exponent=0.25)(q2, q3),
    ]

    for gate in cirq_shared_gates:
        circuit.append(gate)

    # unitary = _unitary_cirq(circuit)
    # cirq_circuit = convert_to_cirq(circuit)

    return circuit


if __name__ == "__main__":

    pass
