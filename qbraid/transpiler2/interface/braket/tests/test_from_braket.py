import numpy as np
import pytest
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction
from braket.circuits import gates as braket_gates

from qbraid.transpiler2.interface.braket.braket_utils import _equal_unitaries
from qbraid.transpiler2.interface.braket.convert_from_braket import from_braket


def test_from_braket_bell_circuit():
    braket_circuit = BKCircuit().h(0).cnot(0, 1)
    cirq_circuit = from_braket(braket_circuit)
    assert _equal_unitaries(braket_circuit, cirq_circuit)


def test_from_braket_non_parameterized_single_qubit_gates():
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
    assert _equal_unitaries(braket_circuit, cirq_circuit)


@pytest.mark.parametrize("qubit_index", (0, 3))
def test_from_braket_parameterized_single_qubit_gates(qubit_index):
    braket_circuit = BKCircuit()
    pgates = [
        braket_gates.Rx,
        braket_gates.Ry,
        braket_gates.Rz,
        braket_gates.PhaseShift,
    ]
    angles = np.random.RandomState(11).random(len(pgates))
    instructions = [Instruction(rot(a), target=qubit_index) for rot, a in zip(pgates, angles)]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)

    assert _equal_unitaries(braket_circuit, cirq_circuit)


def test_from_braket_non_parameterized_two_qubit_gates():
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
    assert _equal_unitaries(braket_circuit, cirq_circuit)


def test_from_braket_parameterized_two_qubit_gates():
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
    angles = np.random.RandomState(2).random(len(pgates))
    instructions = [Instruction(rot(a), target=[0, 1]) for rot, a in zip(pgates, angles)]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert _equal_unitaries(braket_circuit, cirq_circuit)


def test_from_braket_three_qubit_gates():
    braket_circuit = BKCircuit()
    instructions = [
        Instruction(braket_gates.CCNot(), target=[1, 2, 3]),
        Instruction(braket_gates.CSwap(), target=[1, 2, 3]),
    ]
    for instr in instructions:
        braket_circuit.add_instruction(instr)
    cirq_circuit = from_braket(braket_circuit)
    assert _equal_unitaries(braket_circuit, cirq_circuit)


def _rotation_of_pi_over_7(num_qubits):
    matrix = np.identity(2**num_qubits)
    matrix[0:2, 0:2] = [
        [np.cos(np.pi / 7), np.sin(np.pi / 7)],
        [-np.sin(np.pi / 7), np.cos(np.pi / 7)],
    ]
    return matrix


@pytest.mark.skip(reason="Unsupported gates become unitaries.")
def test_from_braket_raises_on_unsupported_gates():
    for num_qubits in range(1, 5):
        braket_circuit = BKCircuit()
        instr = Instruction(
            braket_gates.Unitary(_rotation_of_pi_over_7(num_qubits)),
            target=list(range(num_qubits)),
        )
        braket_circuit.add_instruction(instr)
        with pytest.raises(ValueError):
            from_braket(braket_circuit)
