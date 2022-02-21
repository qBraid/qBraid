"""
Unit tests for the qbraid convert_to_contiguous interfacing
"""

import cirq
import numpy as np
from braket.circuits import Circuit as BraketCircuit

from qbraid.interface import convert_to_contiguous, to_unitary


def test_make_contiguous():
    braket_circuit = BraketCircuit()
    braket_circuit.x(0)
    braket_circuit.y(2)
    braket_circuit.z(4)
    assert braket_circuit.qubit_count == 3

    cirq_circuit = cirq.Circuit()
    q0 = cirq.LineQubit(4)
    q2 = cirq.LineQubit(2)
    q4 = cirq.LineQubit(0)
    cirq_circuit.append(cirq.X(q0))
    cirq_circuit.append(cirq.Y(q2))
    cirq_circuit.append(cirq.Z(q4))
    assert len(cirq_circuit.all_qubits()) == 3

    braket_unitary = to_unitary(braket_circuit, ensure_contiguous=True)
    cirq_unitary = to_unitary(cirq_circuit, ensure_contiguous=True)
    assert np.allclose(braket_unitary, cirq_unitary)

    braket_compat_circuit = convert_to_contiguous(braket_circuit)
    assert braket_compat_circuit.qubit_count == 3

    cirq_compat_circuit = convert_to_contiguous(cirq_circuit)
    assert len(cirq_circuit.all_qubits()) == 3

    braket_compat_unitary = to_unitary(braket_compat_circuit, ensure_contiguous=True)
    cirq_compat_unitary = to_unitary(cirq_compat_circuit, ensure_contiguous=True)
    assert np.allclose(braket_compat_unitary, cirq_compat_unitary)
