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
Unit tests for converting Braket circuits to Cirq circuits via OpenQASM

"""

import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction
from braket.circuits import gates as braket_gates

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_braket.convert_from_braket_qasm import braket_to_qasm3, from_braket
from qbraid.transpiler.exceptions import CircuitConversionError


def test_from_braket_bell_circuit():
    """Test converting bell circuit"""
    # pylint: disable-next=no-member
    braket_circuit = BKCircuit().h(0).cnot(0, 1)
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_from_braket_non_parameterized_single_qubit_gates():
    """Test converting circuit containing non-parameterized single-qubits gates"""
    braket_circuit = BKCircuit()
    instructions = [
        Instruction(braket_gates.I(), target=0),
        Instruction(braket_gates.X(), target=1),
        Instruction(braket_gates.Y(), target=2),
        Instruction(braket_gates.Z(), target=3),
        Instruction(braket_gates.H(), target=0),
        Instruction(braket_gates.S(), target=1),
        Instruction(braket_gates.Si(), target=2),
        Instruction(braket_gates.T(), target=3),
        Instruction(braket_gates.Ti(), target=0),
        Instruction(braket_gates.V(), target=1),
        Instruction(braket_gates.Vi(), target=2),
    ]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubit_index", (0, 3))
def test_from_braket_parameterized_single_qubit_gates(qubit_index):
    """Testing converting circuit containing parameterized single-qubit gates"""
    braket_circuit = BKCircuit()
    pgates = [
        braket_gates.Rx,
        braket_gates.Ry,
        braket_gates.Rz,
        braket_gates.PhaseShift,
    ]
    # pylint: disable-next=no-member
    angles = np.random.RandomState(11).random(len(pgates))
    instructions = [Instruction(rot(a), target=qubit_index) for rot, a in zip(pgates, angles)]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)

    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_from_braket_non_parameterized_two_qubit_gates():
    """Test converting circuit containing non-parameterized two-qubit gates."""
    braket_circuit = BKCircuit()
    instructions = [
        Instruction(braket_gates.CNot(), target=[2, 3]),
        Instruction(braket_gates.Swap(), target=[3, 4]),
        Instruction(braket_gates.ISwap(), target=[2, 3]),
        Instruction(braket_gates.CZ(), target=(3, 4)),
        Instruction(braket_gates.CY(), target=(2, 3)),
    ]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_from_braket_three_qubit_gates():
    """Testing converting circuits containing three-qubit gates"""
    braket_circuit = BKCircuit()
    instructions = [
        Instruction(braket_gates.CCNot(), target=[1, 2, 3]),
        Instruction(braket_gates.CSwap(), target=[1, 2, 3]),
    ]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def _rotation_of_pi_over_7(num_qubits):
    matrix = np.identity(2**num_qubits)
    matrix[0:2, 0:2] = [
        [np.cos(np.pi / 7), np.sin(np.pi / 7)],
        [-np.sin(np.pi / 7), np.cos(np.pi / 7)],
    ]
    return matrix


def test_from_braket_raises_on_unsupported_gates():
    """Test that converting circuit with unsupported gate raises error"""
    for num_qubits in range(1, 5):
        braket_circuit = BKCircuit()
        instr = Instruction(
            braket_gates.Unitary(_rotation_of_pi_over_7(num_qubits)),
            target=list(range(num_qubits)),
        )
        braket_circuit.add_instruction(instr)
        with pytest.raises(CircuitConversionError):
            from_braket(braket_circuit)


def test_braket_to_qasm3__bell_circuit():
    """Test converting braket bell circuit to OpenQASM 3.0 string"""
    qasm_expected = """
OPENQASM 3.0;
bit[2] b;
qubit[2] q;
h q[0];
cnot q[0], q[1];
b[0] = measure q[0];
b[1] = measure q[1];
"""
    bell = BKCircuit().h(0).cnot(0, 1)
    assert qasm_expected.strip("\n") == braket_to_qasm3(bell)
