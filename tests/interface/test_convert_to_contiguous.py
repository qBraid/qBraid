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
Unit tests for converting circuits to use contiguous qubit indexing

"""
import numpy as np
from braket.circuits import Circuit as BKCircuit
from cirq import Circuit, LineQubit, X, Y, Z
from pytket.circuit import Circuit as TKCircuit
from qiskit import QuantumCircuit

from qbraid import circuit_wrapper
from qbraid.interface.circuit_equality import circuits_allclose


def test_remove_idle_qubits_qiskit():
    """Test convert_to_contigious on qiskit circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = circuit_wrapper(circuit)
    qprogram.convert_to_contiguous()
    contig_circuit = qprogram.program
    assert contig_circuit.num_qubits == 2


def test_convert_braket_bell():
    """Test convert_to_contigious on bell circuit"""
    circuit = BKCircuit().h(0).cnot(0, 1)  # pylint: disable=no-member
    h_gate = np.sqrt(1 / 2) * np.array([[1, 1], [1, -1]])
    h_gate_kron = np.kron(np.eye(2), h_gate)
    cnot_gate = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    u_expected = np.einsum("ij,jk->ki", h_gate_kron, cnot_gate)
    qprogram = circuit_wrapper(circuit)
    qprogram.convert_to_contiguous()
    u_little_endian = qprogram.unitary_little_endian()
    assert np.allclose(u_expected, u_little_endian)


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

    qprogram = circuit_wrapper(braket_circuit)
    qprogram.convert_to_contiguous()
    braket_compat_circuit = qprogram.program
    assert braket_compat_circuit.qubit_count == 3

    qprogram = circuit_wrapper(cirq_circuit)
    qprogram.convert_to_contiguous()
    cirq_compat_circuit = qprogram.program
    assert circuits_allclose(braket_compat_circuit, cirq_compat_circuit, strict_gphase=True)

    qprogram = circuit_wrapper(cirq_circuit)
    qprogram.convert_to_contiguous(expansion=True)
    cirq_expanded_circuit = qprogram.program
    assert len(cirq_expanded_circuit.all_qubits()) == 5


def test_braket_control_modifier():
    """Test that converting braket circuits to contiguous qubits works with control modifiers"""
    circuit = BKCircuit().y(target=0, control=1)
    qprogram = circuit_wrapper(circuit)
    qprogram.convert_to_contiguous()
    contig_circuit = qprogram.program
    assert circuit.qubit_count == contig_circuit.qubit_count


def test_remove_blank_wires_pytket():
    """Test wires with no operations from pytket circuit"""
    circuit = TKCircuit(3)
    circuit.H(0)
    circuit.CX(0, 1)
    qprogram = circuit_wrapper(circuit)
    qprogram.convert_to_contiguous()
    contig_circuit = qprogram.program
    assert contig_circuit.n_qubits == 2


def test_convert_qasm3_expansion():
    """Test that convert_to_contiguous for qasm3 string"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
h q[1];
cx q[1], q[3];
"""
    qprogram = circuit_wrapper(qasm3_str)
    qprogram.convert_to_contiguous(expansion=True)
    contig_qasm3_str = qprogram.program
    assert contig_qasm3_str == qasm3_str + """i q[0];\ni q[2];\n"""


def test_convert_qasm3():
    """Test that convert_to_contiguous for qasm3 string"""
    qasm3_str = """
OPENQASM 3;
include "stdgates.inc";
qubit[4] q;
h q[1];
cx q[1], q[3];
"""
    qprogram = circuit_wrapper(qasm3_str)
    qprogram.convert_to_contiguous()
    assert qprogram.num_qubits == 2
