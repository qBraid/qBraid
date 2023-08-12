# Copyright (C) 2023 qBraid
# Copyright (C) Unitary Fund
#
# This file is part of the qBraid-SDK.
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# This file includes code adapted from Mitiq (https://github.com/unitaryfund/mitiq)
# with modifications by qBraid. The original copyright notice is included above.
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for converting Braket circuits to Cirq circuits

"""
import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction
from braket.circuits import gates as braket_gates
from braket.circuits import noises as braket_noise_gate
from cirq import ops as cirq_ops

from qbraid.interface import circuits_allclose, to_unitary
from qbraid.transpiler.cirq_braket.convert_from_braket import (
    from_braket,
    unitary_braket_instruction,
)
from qbraid.transpiler.exceptions import CircuitConversionError


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
    instr_cnot_u = unitary_braket_instruction(instr_cnot_01)
    circuit_expected = BKCircuit().add_instruction(instr_cnot_01)
    circuit_test = BKCircuit().add_instruction(instr_cnot_u)
    u_expected = to_unitary(circuit_expected)
    u_test = to_unitary(circuit_test)
    assert np.allclose(u_expected, u_test)


@pytest.mark.parametrize(
    "noise_gate, target_gate",
    [
        (braket_noise_gate.BitFlip, cirq_ops.BitFlipChannel),
        (braket_noise_gate.PhaseFlip, cirq_ops.PhaseFlipChannel),
        (braket_noise_gate.Depolarizing, cirq_ops.DepolarizingChannel),
    ],
)
def test_single_probability_noise_gate(noise_gate, target_gate):
    """Testing converting circuits containing one-probability noise gates"""
    braket_circuit = BKCircuit()
    probs = np.random.uniform(low=0, high=0.5)  # pylint: disable=no-member
    instructions = Instruction(noise_gate(probs), target=[0])
    braket_circuit.add_instruction(instructions)
    cirq_circuit = from_braket(braket_circuit)
    Gate = list(cirq_circuit.all_operations())[0].gate
    assert type(Gate) == target_gate
    assert Gate.p == probs


@pytest.mark.parametrize(
    "noise_gate, target_gate",
    [
        (braket_noise_gate.AmplitudeDamping, cirq_ops.AmplitudeDampingChannel),
        (braket_noise_gate.PhaseDamping, cirq_ops.PhaseDampingChannel),
    ],
)
def test_single_gamma_noise_gate(noise_gate, target_gate):
    """Testing converting circuits containing one-probability noise gates"""
    braket_circuit = BKCircuit()
    probs = np.random.uniform(low=0, high=0.5)  # pylint: disable=no-member
    instructions = Instruction(noise_gate(probs), target=[0])
    braket_circuit.add_instruction(instructions)
    cirq_circuit = from_braket(braket_circuit)
    Gate = list(cirq_circuit.all_operations())[0].gate
    assert type(Gate) == target_gate
    assert Gate.gamma == probs


def test_kraus_gates():
    """Testing converting Kraus noise gates"""
    K0 = np.sqrt(0.8) * np.eye(4)
    K1 = np.sqrt(0.2) * np.kron(np.array([[0, 1], [1, 0]]), np.array([[0, 1], [1, 0]]))
    instructions = Instruction(braket_noise_gate.Kraus(matrices=[K0, K1]), target=[0, 1])
    braket_circuit = BKCircuit().add_instruction(instructions)
    cirq_circuit = from_braket(braket_circuit)
    Gate = list(cirq_circuit.all_operations())[0].gate
    assert type(Gate) == cirq_ops.kraus_channel.KrausChannel
    assert np.allclose(Gate._kraus_ops, [K0, K1])


def test_generalized_amplitude_damping_channel_gate():
    """Testing converting Kraus noise gates"""
    probs = np.random.uniform(low=0, high=0.5, size=(2))
    instruction = Instruction(
        braket_noise_gate.GeneralizedAmplitudeDamping(gamma=probs[0], probability=probs[1]),
        target=[0],
    )
    braket_circuit = BKCircuit().add_instruction(instruction)
    cirq_circuit = from_braket(braket_circuit)
    Gate = list(cirq_circuit.all_operations())[0].gate
    assert type(Gate) == cirq_ops.GeneralizedAmplitudeDampingChannel
    assert Gate.gamma == probs[0]
    assert Gate.p == probs[1]


def test_depolarizing_channel_gate():
    probs = np.random.uniform(low=0, high=0.5, size=(1))
    instruction = Instruction(
        braket_noise_gate.TwoQubitDepolarizing(probability=probs[0]), target=[0, 1]
    )
    braket_circuit = BKCircuit().add_instruction(instruction)
    cirq_circuit = from_braket(braket_circuit)
    Gate = list(cirq_circuit.all_operations())[0].gate
    assert type(Gate) == cirq_ops.common_channels.DepolarizingChannel
    assert Gate.p == probs
    assert Gate.n_qubits == 2


def test_raise_error():
    with pytest.raises(CircuitConversionError):
        from braket.pulse import Frame, Port
        from braket.pulse.pulse_sequence import PulseSequence

        pre_fram = Frame(
            frame_id="predefined_frame_1",
            frequency=2e9,
            port=Port(port_id="device_port_x0", dt=1e-9, properties={}),
            phase=0,
            is_predefined=True,
        )
        pulse_seq = PulseSequence().set_frequency(pre_fram, 6e6)

        test_case = BKCircuit().add_instruction(
            Instruction(braket_gates.PulseGate(pulse_seq, 1), [0])
        )
        from_braket(test_case)
