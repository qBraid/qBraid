# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for qbraid.programs.qiskit.QiskitCircuit

"""
import pytest
from qiskit import QuantumCircuit

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.qiskit import QiskitCircuit


def test_reverse_qubit_order():
    """Test reversing ordering of qubits in qiskit circuit"""
    circ = QuantumCircuit(3)
    circ.h(0)
    circ.cx(0, 2)

    qprogram = QiskitCircuit(circ)
    qprogram.reverse_qubit_order()
    reversed_circ = qprogram.program

    expected_circ = QuantumCircuit(3)
    expected_circ.h(2)
    expected_circ.cx(2, 0)

    assert (
        reversed_circ == expected_circ
    ), "The reversed circuit does not match the expected output."


def test_remove_idle_qubits_qiskit():
    """Test convert_to_contigious on qiskit circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QiskitCircuit(circuit)
    qprogram.remove_idle_qubits()
    contig_circuit = qprogram.program
    assert contig_circuit.num_qubits == 2


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        QiskitCircuit("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_circuit_properties():
    """Test properties of QiskitCircuit"""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QiskitCircuit(circuit)
    assert len(qprogram.qubits) == 2
    assert qprogram.num_qubits == 2
    assert qprogram.num_clbits == 0
    assert qprogram.depth == 2
