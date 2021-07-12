"""
Unit tests for the qbraid transpiler.
"""
import pytest
import numpy as np
import cirq
from cirq import Circuit as CirqCircuit
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.quantum_info import Operator as QiskitOperator
from braket.circuits import Circuit as BraketCircuit
from braket.circuits.unitary_calculation import calculate_unitary
from qbraid.transpiler2.transpiler import qbraid_wrapper


def to_unitary(circuit):
    """Calculate unitary of a braket, cirq, or qiskit circuit.
    Args:
        circuit (braket, cirq, or qiskit Circuit): The circuit object for which
            the unitary matrix will be calculated.
    Returns:
        numpy.ndarray: A numpy array representing the `circuit` as a unitary
    """
    if isinstance(circuit, BraketCircuit):
        return calculate_unitary(circuit.qubit_count, circuit.instructions)
    elif isinstance(circuit, CirqCircuit):
        return circuit.unitary()
    elif isinstance(circuit, QiskitCircuit):
        return QiskitOperator(circuit).data
    else:
        raise TypeError(f"to_unitary calculation not supported for type {type(circuit)}")


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
    circuit.sxdg(1)
    circuit.iswap(2, 3)
    circuit.swap([0, 1], [2, 3])
    circuit.cx(0, 1)
    circuit.cp(np.pi / 4, 2, 3)

    unitary = to_unitary(circuit)
    qbraid_circuit = qbraid_wrapper(circuit)

    return qbraid_circuit, unitary


def cirq_shared_gates_circuit(rev_qubits=False):
    """Returns cirq `Circuit` for qBraid `TestSharedGates`
    rev_qubits=True reverses ordering of qubits."""

    circuit = CirqCircuit()
    qubits = [cirq.LineQubit(i) for i in range(4)]
    q3, q2, q1, q0 = qubits if rev_qubits else list(reversed(qubits))
    mapping = {q3: 0, q2: 1, q1: 2, q0: 3} if rev_qubits else {q0: 0, q1: 1, q2: 2, q3: 3}

    cirq_gates = [
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
        cirq.Rx(rads=np.pi / 4)(q0),
        cirq.Ry(rads=np.pi / 2)(q1),
        cirq.Rz(rads=3 * np.pi / 4)(q2),
        cirq.ZPowGate(exponent=1 / 8)(q3),
        cirq.XPowGate(exponent=0.5)(q0),
        cirq.XPowGate(exponent=-0.5)(q1),
        cirq.ISWAP(q2, q3),
        cirq.SWAP(q0, q2),
        cirq.SWAP(q1, q3),
        cirq.CNOT(q0, q1),
        cirq.CZPowGate(exponent=0.25)(q2, q3),
    ]

    for gate in cirq_gates:
        circuit.append(gate)

    unitary = to_unitary(circuit)
    qbraid_circuit = qbraid_wrapper(circuit, input_qubit_mapping=mapping)

    return qbraid_circuit, unitary


def braket_shared_gates_circuit():
    """Returns braket `Circuit` for qBraid `TestSharedGates`."""

    circuit = BraketCircuit()

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.si(1)
    circuit.t(2)
    circuit.ti(3)
    circuit.rx(0, np.pi / 4)
    circuit.ry(1, np.pi / 2)
    circuit.rz(2, 3 * np.pi / 4)
    circuit.phaseshift(3, np.pi / 8)
    circuit.v(0)
    circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    unitary = to_unitary(circuit)
    qbraid_circuit = qbraid_wrapper(circuit)

    return qbraid_circuit, unitary


# Define circuits and unitaries
qbraid_circuit_braket, braket_unitary = braket_shared_gates_circuit()
qbraid_circuit_cirq, cirq_unitary = cirq_shared_gates_circuit()
qbraid_circuit_cirq_rev, cirq_rev_unitary = cirq_shared_gates_circuit(rev_qubits=True)
qbraid_circuit_qiskit, qiskit_unitary = qiskit_shared_gates_circuit()

cirq_qiskit_equal = np.allclose(cirq_rev_unitary, qiskit_unitary)
cirq_braket_equal = np.allclose(cirq_rev_unitary, braket_unitary)
qiskit_braket_equal = np.allclose(qiskit_unitary, braket_unitary)
assert cirq_qiskit_equal and cirq_braket_equal and qiskit_braket_equal

data_test_shared_gates = [
    (qbraid_circuit_braket, "cirq", cirq_unitary),
    (qbraid_circuit_braket, "qiskit", qiskit_unitary),
    (qbraid_circuit_qiskit, "braket", braket_unitary),
    (qbraid_circuit_qiskit, "cirq", cirq_unitary),
    (qbraid_circuit_cirq, "braket", braket_unitary),
    (qbraid_circuit_cirq, "qiskit", qiskit_unitary),
]


@pytest.mark.parametrize("qbraid_circuit,target_package,target_unitary", data_test_shared_gates)
def test_shared_gates(qbraid_circuit, target_package, target_unitary):
    """Tests transpiling circuits composed of gate types that share explicit support across
    multiple qbraid tranpsiler supported packages (qiskit, cirq, braket).
    """
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    assert np.allclose(transpiled_unitary, target_unitary)
