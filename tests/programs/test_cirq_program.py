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
Unit tests for qbraid.programs.cirq.CirqCircuit

"""
from cirq import CNOT, Circuit, GridQubit, H, LineQubit, Moment, NamedQubit, X, Y, Z

from qbraid.programs.cirq import CirqCircuit
from qbraid.programs.testing import circuits_allclose


def test_contiguous_line_qubits():
    """Test convert to contiguous method for line qubits."""
    circuit = Circuit()
    circuit.append(X(LineQubit(0)))
    circuit.append(Y(LineQubit(2)))
    circuit.append(Z(LineQubit(4)))

    program = CirqCircuit(circuit)
    program.remove_idle_qubits()

    expected_qubits = [LineQubit(0), LineQubit(1), LineQubit(2)]
    assert set(program.qubits) == set(expected_qubits)


def test_contiguous_grid_qubits():
    """Test convert to contiguous method for grid qubits."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(0, 2)))
    circuit.append(Z(GridQubit(0, 4)))

    program = CirqCircuit(circuit)
    program.remove_idle_qubits()

    expected_qubits = [GridQubit(0, 0), GridQubit(0, 1), GridQubit(0, 2)]
    assert set(program.qubits) == set(expected_qubits)


def test_mixed_qubit_types():
    """Test convert to contiguous method raises error for mixed qubit type."""
    circuit = Circuit()
    circuit.append(X(LineQubit(3)))
    circuit.append(Y(GridQubit(0, 4)))

    program = CirqCircuit(circuit)
    program.remove_idle_qubits()

    expected_qubits = [LineQubit(0), LineQubit(1)]
    assert set(program.qubits) == set(expected_qubits)


def test_convert_named_qubit_to_line_qubit():
    """Test converting a circuit of all NamedQubits to LineQubits"""
    circuit = Circuit(
        [
            Moment(H(NamedQubit("q"))),
        ]
    )

    program = CirqCircuit(circuit)
    program._convert_to_line_qubits()
    for qubit in program.qubits:
        assert isinstance(qubit, LineQubit)


def test_reverse_named_qubit_order():
    """Test reversing the order of qubits in a NamedQubit circuit"""
    circuit = Circuit(
        [
            Moment(H(NamedQubit("q"))),
            Moment(X(NamedQubit("y"))),
        ]
    )

    op_map = {}
    for op in circuit.all_operations():
        op_map[str(op.gate)] = op.qubits

    program = CirqCircuit(circuit)
    program.reverse_qubit_order()
    rev_circuit = program.program
    for op in rev_circuit.all_operations():
        assert op_map[str(op.gate)] != op.qubits


def test_remove_idle_named_qubits():
    """Test removing idle qubits from a NamedQubit circuit"""
    circuit = Circuit(
        [
            Moment(H(NamedQubit("q_4")), H(NamedQubit("q_8"))),
            Moment(CNOT(NamedQubit("q_6"), NamedQubit("q_8"))),
            Moment(X(NamedQubit("q_2"))),
        ]
    )
    qprogram = CirqCircuit(circuit)
    qprogram.remove_idle_qubits()
    new_circuit = qprogram.program
    assert set(new_circuit.all_qubits()) == {NamedQubit(str(i)) for i in range(qprogram.num_qubits)}
    assert circuits_allclose(circuit, new_circuit)
