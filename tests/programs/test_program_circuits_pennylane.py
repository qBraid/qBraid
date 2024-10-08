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
Unit tests for qbraid.programs.pennylane.PennylaneTape

"""
import numpy as np
import pennylane as qml
import pytest
from pennylane.tape import QuantumTape

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.pennylane import PennylaneTape


def two_wire_tape(wire1, wire2):
    """Returns a simple Pennylane tape with two wires."""
    with QuantumTape() as tape:
        qml.Hadamard(wires=wire1)
        qml.CNOT(wires=[wire1, wire2])
    return tape


@pytest.mark.parametrize("bell_circuit", ["pennylane"], indirect=True)
def test_pennylane_tape(bell_circuit, bell_unitary):
    """Test PennylaneTape class."""
    tape, _ = bell_circuit
    program = PennylaneTape(tape)
    assert isinstance(program.program, QuantumTape)
    assert program.qubits == [0, 1]
    assert program.num_qubits == 2
    assert program.num_clbits == 0
    assert program.depth == 2
    assert np.allclose(program.unitary(), bell_unitary)


@pytest.mark.parametrize("wires", [(0, 1), ("a", "b")])
def test_pennylane_reverse_qubit_order(wires):
    """Test PennylaneTape class with qubits in reverse order."""
    w1, w2 = wires

    tape_in = two_wire_tape(w1, w2)
    tape_expected = two_wire_tape(w2, w1)

    wires_in = [op.wires for op in tape_in.operations]
    wires_expected = [op.wires for op in tape_expected.operations]

    assert wires_in != wires_expected

    program = PennylaneTape(tape_in)
    program.reverse_qubit_order()
    tape_out = program.program

    wires_out = [op.wires for op in tape_out.operations]

    assert wires_out == wires_expected
    assert str(tape_out) == str(tape_expected)
    assert repr(tape_out) == repr(tape_expected)
    assert qml.equal(tape_out, tape_expected)


@pytest.mark.parametrize("wires", [(3, 6), (2, 4)])
def test_pennylane_remove_idle_qubits(wires):
    """Test PennylaneTape class with qubits in reverse order."""
    tape_in = two_wire_tape(*wires)
    program = PennylaneTape(tape_in)
    program.remove_idle_qubits()
    tape_out = program.program

    wires_out = [op.wires.tolist() for op in tape_out.operations]

    assert wires_out == [[0], [0, 1]]
    assert tape_out.wires.toset() == {0, 1}


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        PennylaneTape("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")
