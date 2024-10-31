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
Unit tests for qbraid.programs.cirq.CirqCircuit

"""
from typing import Any
from unittest.mock import Mock

import cirq
import pytest
from cirq import CNOT, Circuit, GridQubit, H, LineQubit, Moment, NamedQubit, X, Y, Z

from qbraid.interface import circuits_allclose
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.cirq import CirqCircuit


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
    assert program.num_clbits == 0


def test_remove_idle_grid_qubits_row():
    """Test convert to contiguous method for grid qubits."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(0, 2)))
    circuit.append(Z(GridQubit(0, 4)))

    program = CirqCircuit(circuit)
    program.remove_idle_qubits()

    expected_qubits = [GridQubit(0, 0), GridQubit(0, 1), GridQubit(0, 2)]
    assert set(program.qubits) == set(expected_qubits)


def test_remove_idle_grid_qubits_col():
    """Test convert to contiguous method for grid qubits."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(2, 0)))
    circuit.append(Z(GridQubit(4, 0)))

    program = CirqCircuit(circuit)
    program.remove_idle_qubits()

    expected_qubits = [GridQubit(0, 0), GridQubit(1, 0), GridQubit(2, 0)]
    assert set(program.qubits) == set(expected_qubits)


@pytest.mark.parametrize("index1,index2", [(1, 2), (2, 1)])
def test_remove_idle_qubits_raises(index1, index2):
    """Test removing idle qubits for grid qubits raises exception if
    row or col indicies are not all equal."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(index1, index2)))

    program = CirqCircuit(circuit)

    with pytest.raises(ValueError):
        program.remove_idle_qubits()


def test_convert_grid_to_line_qubits():
    """Test converting grid qubits to line qubits."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(0, 1)))
    circuit.append(Z(GridQubit(0, 2)))

    program = CirqCircuit(circuit)
    program._convert_to_line_qubits()

    expected_qubits = [LineQubit(0), LineQubit(1), LineQubit(2)]
    assert set(program.qubits) == set(expected_qubits)

    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(1, 0)))
    circuit.append(Z(GridQubit(2, 0)))

    program = CirqCircuit(circuit)
    program._convert_to_line_qubits()

    expected_qubits = [LineQubit(0), LineQubit(1), LineQubit(2)]
    assert set(program.qubits) == set(expected_qubits)

    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(1, 1)))
    circuit.append(Z(GridQubit(2, 2)))

    program = CirqCircuit(circuit)
    program._convert_to_line_qubits()

    expected_qubits = [LineQubit(0), LineQubit(1), LineQubit(2)]
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


def test_remove_all_measurements():
    """Test removing all measurement gates from a circuit"""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, key="m0"), cirq.measure(q1, key="m1")
    )
    expected_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    result_circuit = CirqCircuit.remove_measurements(circuit)
    assert result_circuit == expected_circuit, "All measurement gates should be removed."


def test_no_measurements_to_remove():
    """Test removing measurements from a circuit with no measurements"""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    result_circuit = CirqCircuit.remove_measurements(circuit)
    assert (
        result_circuit == circuit
    ), "The circuit should remain unchanged as there are no measurements."


def test_mixed_operations_and_measurements():
    """Test removing measurements from a circuit with mixed operations and measurements"""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0), cirq.measure(q0, key="m0"), cirq.CNOT(q0, q1), cirq.measure(q1, key="m1")
    )
    expected_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    result_circuit = CirqCircuit.remove_measurements(circuit)
    assert (
        result_circuit == expected_circuit
    ), "All measurement gates should be removed, leaving other operations intact."


def test_align_final_measurements():
    """Test aligning measurements for a circuit with measurements."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, key="m0"), cirq.measure(q1, key="m1")
    )
    expected_circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.Moment(cirq.measure(q0, key="m0"), cirq.measure(q1, key="m1")),
    )
    aligned_circuit = CirqCircuit.align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The measurements should be aligned in the same moment"


def test_align_measurements_for_no_measurement():
    """Test aligning measurements for a circuit with no measurements."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    expected_circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    aligned_circuit = CirqCircuit.align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The circuit should remain unchanged as there are no measurements"


def test_align_measurements_for_partial_measurement():
    """Test aligning measurements from a circuit where not all qubits are measured."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, key="m0"))
    expected_circuit = circuit
    aligned_circuit = CirqCircuit.align_final_measurements(circuit)
    assert (
        aligned_circuit == expected_circuit
    ), "The circuit should remain unchanged as not all qubits are measured"


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        CirqCircuit("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_key_from_line_qubit():
    """Test generating a key from a LineQubit."""
    qubit = cirq.LineQubit(1)
    expected_key = "q(1)"
    assert CirqCircuit._key_from_qubit(qubit) == expected_key


def test_key_from_grid_qubit():
    """Test generating a key from a GridQubit."""
    qubit = cirq.GridQubit(3, 5)
    expected_key = "3"
    assert CirqCircuit._key_from_qubit(qubit) == expected_key


def test_key_from_named_qubit():
    """Test generating a key from a NamedQubit."""
    qubit = cirq.NamedQubit("qubit7")
    expected_key = "qubit7"
    assert CirqCircuit._key_from_qubit(qubit) == expected_key


def test_key_from_unsupported_qubit():
    """Test generating a key from an unsupported qubit type."""

    class UnsupportedQubit(cirq.Qid):
        """Unsupported qubit type for testing."""

        def _comparison_key(self) -> Any:
            """Dummy abstract method implemented for testing."""
            return 0

        def dimension(self) -> int:
            """Dummy abstract method implemented for testing."""
            return 0

    qubit = UnsupportedQubit()
    with pytest.raises(ValueError) as excinfo:
        CirqCircuit._key_from_qubit(qubit)

    expected_message = "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
    assert expected_message in str(excinfo.value)


def test_int_from_qubit_grid_qubit():
    """Test generating an integer key from a GridQubit."""
    qubit = cirq.GridQubit(3, 5)
    expected_key = 3
    assert CirqCircuit._int_from_qubit(qubit) == expected_key


def test_bad_qubit():
    """Test qubits that aren't a GridQubit, LineQubit, or NamedQubit."""
    qubit = "bad qubit"
    with pytest.raises(ValueError) as excinfo:
        CirqCircuit._int_from_qubit(qubit)
    expected_message = "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
    assert expected_message in str(excinfo.value)

    qubits = [qubit]
    targets = [0]
    with pytest.raises(ValueError) as excinfo:
        CirqCircuit._make_qubits(qubits, targets)


def test_transform_no_effect():
    """Test that transform method has no effect
    since it is not implemented"""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.I(qubit))
    program = CirqCircuit(circuit)
    device = Mock()
    program.transform(device)
    assert program.program == circuit
