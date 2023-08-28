# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for the qbraid convert_to_contiguous interfacing

"""
import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from cirq import Circuit, LineQubit, X, Y, Z
from pytket.circuit import Circuit as TKCircuit
from qiskit import QuantumCircuit

from qbraid.exceptions import ProgramTypeError
from qbraid.interface.calculate_unitary import circuits_allclose
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


def test_remove_idle_qubits_qiskit():
    """Test convert_to_contigious on qiskit circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    contig_circuit = convert_to_contiguous(circuit)
    assert contig_circuit.num_qubits == 2


def test_convert_braket_bell():
    """Test convert_to_contigious on bell circuit"""
    circuit = BKCircuit().h(0).cnot(0, 1)  # pylint: disable=no-member
    h_gate = np.sqrt(1 / 2) * np.array([[1, 1], [1, -1]])
    h_gate_kron = np.kron(np.eye(2), h_gate)
    cnot_gate = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    u_expected = np.einsum("ij,jk->ki", h_gate_kron, cnot_gate)
    contig_circuit = convert_to_contiguous(circuit)
    u_test = contig_circuit.as_unitary()
    assert np.allclose(u_expected, u_test)


def test_compare_conversion_braket_cirq():
    """Test unitary equivalance after converting to contiguous qubits"""
    # pylint: disable=no-member
    braket_circuit = BKCircuit()
    braket_circuit.x(0)
    braket_circuit.y(2)
    braket_circuit.z(4)
    # pylint: enable=no-member
    assert braket_circuit.qubit_count == 3

    cirq_circuit = Circuit()
    q0 = LineQubit(0)
    q2 = LineQubit(2)
    q4 = LineQubit(4)
    cirq_circuit.append(X(q0))
    cirq_circuit.append(Y(q2))
    cirq_circuit.append(Z(q4))
    assert len(cirq_circuit.all_qubits()) == 3

    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)

    braket_compat_circuit = convert_to_contiguous(braket_circuit)
    assert braket_compat_circuit.qubit_count == 3

    cirq_compat_circuit = convert_to_contiguous(cirq_circuit)

    assert circuits_allclose(braket_compat_circuit, cirq_compat_circuit, strict_gphase=True)

    cirq_expanded_circuit = convert_to_contiguous(cirq_circuit, expansion=True)
    assert len(cirq_expanded_circuit.all_qubits()) == 5


def test_braket_control_modifier():
    """Test that converting braket circuits to contiguous qubits works with control modifiers"""
    circuit = BKCircuit().y(target=0, control=1)
    contrig_circuit = convert_to_contiguous(circuit)
    assert circuit.qubit_count == contrig_circuit.qubit_count


def test_remove_blank_wires_pytket():
    circuit = TKCircuit(3)
    circuit.H(0)
    circuit.CX(0, 1)
    contig_circuit = convert_to_contiguous(circuit)
    assert contig_circuit.n_qubits == 2


def test_unitary_raises():
    with pytest.raises(ProgramTypeError):
        convert_to_contiguous(None)
