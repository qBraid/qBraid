"""
Unit tests for the qbraid convert_to_contiguous interfacing
"""
import cirq
import pytest
from braket.circuits import Circuit as BraketCircuit

from qbraid.interface.calculate_unitary import equal_unitaries
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


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

    assert equal_unitaries(braket_circuit, cirq_circuit)

    braket_compat_circuit = convert_to_contiguous(braket_circuit)
    assert braket_compat_circuit.qubit_count == 3

    cirq_compat_circuit = convert_to_contiguous(cirq_circuit)
    assert len(cirq_circuit.all_qubits()) == 3

    assert equal_unitaries(braket_compat_circuit, cirq_compat_circuit)
