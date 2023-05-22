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
Unit tests for converting Cirq circuits to Braket circuits

"""
import numpy as np
import pytest
from braket.circuits import noises as braket_noise_gate
from cirq import Circuit, LineQubit, ops, testing

from qbraid.interface import circuits_allclose, random_unitary_matrix
from qbraid.transpiler.cirq_braket.convert_to_braket import to_braket


@pytest.mark.parametrize("qreg", (LineQubit.range(2), [LineQubit(1), LineQubit(6)]))
def test_to_braket_bell_circuit(qreg):
    """Test converting bell circuit"""
    cirq_circuit = Circuit(ops.H(qreg[0]), ops.CNOT(*qreg))
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_to_braket_non_parameterized_single_qubit_gates():
    """Test converting circuit containing non-parameterized single-qubits gates"""
    qreg = LineQubit.range(4)
    cirq_circuit = Circuit(
        ops.I(qreg[0]),
        ops.X(qreg[1]),
        ops.Y(qreg[2]),
        ops.Z(qreg[3]),
        ops.H(qreg[0]),
        ops.S(qreg[1]),
        ops.S(qreg[2]) ** -1,
        ops.T(qreg[3]),
        ops.T(qreg[0]) ** -1,
        ops.X(qreg[1]) ** 0.5,
        ops.X(qreg[2]) ** -0.5,
    )
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubit_index", (0, 3))
def test_to_braket_parameterized_single_qubit_gates(qubit_index):
    """Testing converting circuit containing parameterized single-qubit gates"""
    qubit = LineQubit(qubit_index)
    angles = np.random.RandomState(11).random(4)  # pylint: disable=no-member
    cirq_circuit = Circuit(
        ops.rx(angles[0]).on(qubit),
        ops.ry(angles[1]).on(qubit),
        ops.rz(angles[2]).on(qubit),
        ops.Z.on(qubit) ** (angles[3] / np.pi),
    )
    braket_circuit = to_braket(cirq_circuit)
    print(braket_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_to_braket_non_parameterized_two_qubit_gates():
    """Test converting circuit containing non-parameterized two-qubit gates."""
    qreg = LineQubit.range(2, 5)
    cirq_circuit = Circuit(
        ops.CNOT(*qreg[:2]),
        ops.SWAP(*qreg[1:]),
        ops.ISWAP(*qreg[:2]),
        ops.CZ(*qreg[1:]),
        ops.ControlledGate(ops.Y).on(*qreg[:2]),
    )
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_to_braket_three_qubit_gates():
    """Testing converting circuits containing three-qubit gates"""
    qreg = LineQubit.range(1, 4)
    cirq_circuit = Circuit(ops.TOFFOLI(*qreg), ops.FREDKIN(*qreg))
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


def test_to_braket_common_one_qubit_gates():
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    rots = [ops.rx, ops.ry, ops.rz]
    angles = [1 / 5, 3 / 5, -4 / 5]
    qubit = LineQubit(0)
    cirq_circuit = Circuit(
        # Paulis.
        ops.X(qubit),
        ops.Y(qubit),
        ops.Z(qubit),
        # Single-qubit rotations.
        [rot(angle).on(qubit) for rot, angle in zip(rots, angles)],
        # Rz alter egos.
        ops.T(qubit),
        ops.T(qubit) ** -1,
        ops.S(qubit),
        ops.S(qubit) ** -1,
        # Rx alter egos.
        ops.X(qubit) ** 0.5,
        ops.X(qubit) ** -0.5,
    )

    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("uncommon_gate", [ops.HPowGate(exponent=-1 / 14)])
def test_to_braket_uncommon_one_qubit_gates(uncommon_gate):
    """These gates get decomposed when converting Cirq -> Braket, but
    the unitaries should be equal up to global phase.
    """
    cirq_circuit = Circuit(uncommon_gate.on(LineQubit(0)))
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(
        cirq_circuit,
        braket_circuit,
        atol=1e-7,
    )


@pytest.mark.parametrize(
    "common_gate",
    [
        ops.CNOT,
        ops.CZ,
        ops.ISWAP,
        ops.XXPowGate(exponent=-0.2),
        ops.YYPowGate(exponent=0.3),
        ops.ZZPowGate(exponent=-0.1),
    ],
)
def test_to_braket_common_two_qubit_gates(common_gate):
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    cirq_circuit = Circuit(common_gate.on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    if not isinstance(common_gate, (ops.XXPowGate, ops.YYPowGate, ops.ZZPowGate)):
        assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)
    else:
        assert circuits_allclose(braket_circuit, cirq_circuit)


@pytest.mark.parametrize(
    "uncommon_gate",
    [ops.CNotPowGate(exponent=-1 / 17), ops.CZPowGate(exponent=2 / 7)],
)
def test_to_braket_uncommon_two_qubit_gates(uncommon_gate):
    """These gates get decomposed when converting Cirq -> Braket, but
    the unitaries should be equal up to global phase.
    """
    cirq_circuit = Circuit(uncommon_gate.on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit)


@pytest.mark.parametrize(
    "common_gate",
    [
        ops.TOFFOLI,
        ops.FREDKIN,
    ],
)
def test_to_braket_common_three_qubit_gates(common_gate):
    """These gates should stay the same (i.e., not get decomposed) when
    converting Cirq -> Braket.
    """
    cirq_circuit = Circuit(common_gate.on(*LineQubit.range(3)))
    braket_circuit = to_braket(cirq_circuit)
    assert circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_50_random_circuits(num_qubits):
    """Testing converting 50 random circuits"""
    for i in range(10):
        moments = np.random.randint(1, 6)
        state = num_qubits + i
        cirq_circuit = testing.random_circuit(
            num_qubits, n_moments=moments, op_density=1, random_state=state
        )
        braket_circuit = to_braket(cirq_circuit)
        if not circuits_allclose(braket_circuit, cirq_circuit, strict_gphase=True):
            assert False
    assert True


@pytest.mark.parametrize(
    "noise_gate, target_gate",
    [
        (ops.BitFlipChannel, braket_noise_gate.BitFlip),
        (ops.PhaseFlipChannel, braket_noise_gate.PhaseFlip),
        (ops.DepolarizingChannel, braket_noise_gate.Depolarizing),
    ],
)
def test_to_braket_single_probability_noise_gate(noise_gate, target_gate):
    """Test transpile single arg noise braket"""
    probs = np.random.uniform(low=0, high=0.5)
    cirq_circuit = Circuit(noise_gate(probs).on(*LineQubit.range(1)))
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == target_gate
    assert Gate.qubit_count == 1
    assert Gate.probability == probs


@pytest.mark.parametrize(
    "noise_gate, target_gate",
    [
        (ops.AmplitudeDampingChannel, braket_noise_gate.AmplitudeDamping),
        (ops.PhaseDampingChannel, braket_noise_gate.PhaseDamping),
    ],
)
def test_to_braket_single_gamma_noise_gate(noise_gate, target_gate):
    """Test transpile single arg noise braket"""
    probs = np.random.uniform(low=0, high=0.5)
    cirq_circuit = Circuit(noise_gate(probs).on(*LineQubit.range(1)))
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == target_gate
    assert Gate.qubit_count == 1
    assert Gate.gamma == probs


def test_to_braket_GeneralizedAmplitudeDampingChannel():
    """Test two arg noise gate"""
    probs = np.random.uniform(low=0, high=0.5, size=(2))
    cirq_circuit = Circuit(
        ops.GeneralizedAmplitudeDampingChannel(probs[0], probs[1]).on(*LineQubit.range(1))
    )
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == braket_noise_gate.GeneralizedAmplitudeDamping
    assert Gate.qubit_count == 1
    assert Gate.probability == probs[0]
    assert Gate.gamma == probs[1]


def test_to_braket_DepolarizingChannel():
    """Test DepolarizingChannel"""
    probs = np.random.uniform(low=0, high=0.5, size=(1))
    cirq_circuit = Circuit(ops.DepolarizingChannel(probs[0]).on(*LineQubit.range(1)))
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == braket_noise_gate.Depolarizing
    assert Gate.qubit_count == 1
    assert Gate.probability == probs


def test_to_braket_two_DepolarizingChannel():
    probs = np.random.uniform(low=0, high=0.5, size=(1))
    cirq_circuit = Circuit(ops.DepolarizingChannel(probs[0], n_qubits=2).on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == braket_noise_gate.TwoQubitDepolarizing
    assert Gate.qubit_count == 2
    assert Gate.probability == probs


def test_to_braket_kraus_gates():
    """Test Kraus"""
    K0 = np.sqrt(0.8) * np.eye(4)
    K1 = np.sqrt(0.2) * np.kron(np.array([[0, 1], [1, 0]]), np.array([[0, 1], [1, 0]]))
    cirq_circuit = Circuit(ops.KrausChannel([K0, K1]).on(*LineQubit.range(2)))
    braket_circuit = to_braket(cirq_circuit)
    Gate = braket_circuit.instructions[0].operator
    assert type(Gate) == braket_noise_gate.Kraus
    assert Gate.qubit_count == 2
    assert np.allclose(Gate._matrices, [K0, K1])


def test_braket_unitary_display_name():
    """Test braket unitary gate uses correct display name"""
    unitary = random_unitary_matrix(2)
    braket_circuit = to_braket(Circuit(ops.MatrixGate(unitary).on(LineQubit(0))))
    assert braket_circuit.instructions[0].operator.ascii_symbols[0] == "U"
