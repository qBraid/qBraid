# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for converting Braket circuits to Cirq circuits

"""
import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction
from braket.circuits import gates as braket_gates
from braket.circuits import noises as braket_noise_gate

from qbraid.interface import circuits_allclose, to_unitary
from qbraid.transpiler.cirq_braket.convert_from_braket import (
    from_braket,
    unitary_braket_instruction,
)


def test_from_braket_bell_circuit():
    """Test converting bell circuit"""
    braket_circuit = BKCircuit().h(0).cnot(0, 1)  # pylint: disable=no-member
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
    angles = np.random.RandomState(11).random(len(pgates))  # pylint: disable=no-member
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


def test_from_braket_parameterized_two_qubit_gates():
    """Test converting circuit containing parameterized two-qubit gates."""
    braket_circuit = BKCircuit()
    pgates = [
        braket_gates.CPhaseShift,
        braket_gates.CPhaseShift00,
        braket_gates.CPhaseShift01,
        braket_gates.CPhaseShift10,
        braket_gates.PSwap,
        braket_gates.XX,
        braket_gates.YY,
        braket_gates.ZZ,
        braket_gates.XY,
    ]
    angles = np.random.RandomState(2).random(len(pgates))  # pylint: disable=no-member
    instructions = [Instruction(rot(a), target=[0, 1]) for rot, a in zip(pgates, angles)]
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


def test_unitary_braket_instruction():
    """Test converting Braket instruction to instruction using unitary gate."""
    instr_cnot_01 = Instruction(braket_gates.CNot(), target=[0, 1])
    instr_cnot_10 = Instruction(braket_gates.CNot(), target=[1, 0])
    instr_cnot_u = unitary_braket_instruction(instr_cnot_10)
    circuit_expected = BKCircuit().add_instruction(instr_cnot_01)
    circuit_test = BKCircuit().add_instruction(instr_cnot_u)
    u_expected = to_unitary(circuit_expected)
    u_test = to_unitary(circuit_test)
    assert np.allclose(u_expected, u_test)


def test_single_probability_noise_gate():
    """Testing converting circuits containing one-probability noise gates"""
    braket_circuit = BKCircuit()
    pgates = [
        braket_noise_gate.BitFlip,
        braket_noise_gate.PhaseFlip,
        braket_noise_gate.Depolarizing,
        braket_noise_gate.AmplitudeDamping,
        braket_noise_gate.PhaseDamping,
        braket_noise_gate.PhaseDamping,
    ]
    probs = np.random.rand(len(pgates))  # pylint: disable=no-member
    instructions = [Instruction(rot(p), target=[0]) for rot, p in zip(pgates, probs)]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_kraus_gates():
    """Testing converting Kraus noise gates"""
    K0 = np.sqrt(0.8) * np.eye(4)
    K1 = np.sqrt(0.2) * np.kron(np.array([[0, 1], [1, 0]]), np.array([[0, 1], [1, 0]]))
    braket_circuit = BKCircuit().kraus(targets=(0, 1), matrices=[K0, K1])
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_GeneralizedAmplitudeDampingChannel_gate():
    """Testing converting Kraus noise gates"""
    probs = np.random.rand(2)
    braket_circuit = BKCircuit().generalized_amplitude_damping(
        target=0, gamma=probs[0], probability=probs[1]
    )
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_DepolarizingChannel_gate():
    probs = np.random.rand(1)
    braket_circuit = BKCircuit().two_qubit_depolarizing(target1=0, target2=1, probability=probs[0])
    cirq_circuit = from_braket(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)
