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
Module for converting Cirq circuits to Braket circuits

"""
from typing import Dict, List

import numpy as np
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction as BKInstruction
from braket.circuits import gates as braket_gates
from braket.circuits import noises as braket_noise_gate
from cirq import Circuit, LineQubit
from cirq import ops as cirq_ops
from cirq import protocols

try:
    import cirq_ionq.ionq_native_gates as cirq_ionq_ops
except ImportError:
    cirq_ionq_ops = None

from qbraid.transpiler.custom_gates import matrix_gate
from qbraid.transpiler.exceptions import CircuitConversionError


def _gate_to_matrix_braket(gate: braket_gates.Unitary) -> np.ndarray:
    matrix = gate.to_matrix()
    unitary_gate = braket_gates.Unitary(matrix)
    nqubits = int(np.log2(len(matrix)))
    qubits = list(range(nqubits)) if nqubits > 1 else 0
    circuit = BKCircuit([BKInstruction(unitary_gate, qubits)])
    return circuit.to_unitary()


def unitary_braket_instruction(instr: BKInstruction) -> BKInstruction:
    """Converts a Braket instruction to a unitary gate instruction.

    Args:
        instr: Braket instruction to convert.

    Raises:
        CircuitConversionError: If the instruction cannot be converted
    """
    gate = instr.operator

    try:
        matrix = _gate_to_matrix_braket(gate)
        gate_name = "U" if gate.name is None else gate.name
        return BKInstruction(braket_gates.Unitary(matrix, display_name=gate_name), instr.target)
    except (ValueError, TypeError) as err:
        raise CircuitConversionError(f"Unable to convert the instruction {instr}.") from err


def from_braket(circuit: BKCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.
    """
    from qbraid import circuit_wrapper  # pylint: disable=import-outside-toplevel

    qprogram = circuit_wrapper(circuit)
    qprogram.convert_to_contiguous()
    compat_circuit = qprogram.program
    cirq_qubits = [LineQubit(x) for x in range(len(compat_circuit.qubits))]
    qubit_mapping = {x: cirq_qubits[x] for x in range(len(cirq_qubits))}
    return Circuit(
        _from_braket_instruction(instr, qubit_mapping) for instr in compat_circuit.instructions
    )


def _from_braket_instruction(
    instr: BKInstruction, qubit_mapping: Dict[int, LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the braket instruction to an equivalent Cirq operation or list
    of Cirq operations.

    Args:
        instr: Braket instruction to convert.
        qubit_mapping: Braket qubit indicies mapped to indexed Cirq LineQubits

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
        CircuitConversionError: If error raise during conversion.
    """
    nqubits = len(instr.target)
    BK_qubits = [int(q) for q in instr.target]
    qubits = [qubit_mapping[x] for x in BK_qubits]

    try:
        if nqubits == 1:
            return _from_one_qubit_braket_instruction(instr, qubits)

        if nqubits == 2:
            return _from_two_qubit_braket_instruction(instr, qubits)

        if nqubits == 3:
            if isinstance(instr.operator, braket_gates.CCNot):
                return [cirq_ops.TOFFOLI.on(*qubits)]
            if isinstance(instr.operator, braket_gates.CSwap):
                return [cirq_ops.FREDKIN.on(*qubits)]
            try:
                matrix = _gate_to_matrix_braket(instr.operator)
                return [cirq_ops.MatrixGate(matrix).on(*qubits)]
            except (ValueError, TypeError) as err:
                raise CircuitConversionError(
                    f"Unable to convert the instruction {instr} to Cirq."
                ) from err

        # Unknown instructions.
        raise CircuitConversionError(
            f"Unable to convert to Cirq due to unrecognized \
            instruction: {instr}."
        )
    except Exception as err:
        raise CircuitConversionError(
            f"qBraid transpiler doesn't support operator {instr.operator}"
        ) from err


def _from_one_qubit_braket_instruction(
    instr: BKInstruction, qubits: List[LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the one-qubit Braket instruction to Cirq operation(s).

    Args:
        instr: One-qubit Braket instruction to convert.
        qubits: Cirq LineQubit list indexed according to Braket instruction

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
    """
    gate = instr.operator

    # One-qubit non-parameterized gates.
    if isinstance(gate, braket_gates.I):
        return [cirq_ops.I.on(*qubits)]
    if isinstance(gate, braket_gates.X):
        return [cirq_ops.X.on(*qubits)]
    if isinstance(gate, braket_gates.Y):
        return [cirq_ops.Y.on(*qubits)]
    if isinstance(gate, braket_gates.Z):
        return [cirq_ops.Z.on(*qubits)]
    if isinstance(gate, braket_gates.H):
        return [cirq_ops.H.on(*qubits)]
    if isinstance(gate, braket_gates.S):
        return [cirq_ops.S.on(*qubits)]
    if isinstance(gate, braket_gates.Si):
        return [protocols.inverse(cirq_ops.S.on(*qubits))]
    if isinstance(gate, braket_gates.T):
        return [cirq_ops.T.on(*qubits)]
    if isinstance(gate, braket_gates.Ti):
        return [protocols.inverse(cirq_ops.T.on(*qubits))]
    if isinstance(gate, braket_gates.V):
        return [cirq_ops.X.on(*qubits) ** 0.5]
    if isinstance(gate, braket_gates.Vi):
        return [cirq_ops.X.on(*qubits) ** -0.5]

    # One-qubit parameterized gates.
    if isinstance(gate, braket_gates.Rx):
        return [cirq_ops.rx(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.Ry):
        return [cirq_ops.ry(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.Rz):
        return [cirq_ops.rz(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.PhaseShift):
        return [cirq_ops.Z.on(*qubits) ** (gate.angle / np.pi)]

    # One-qubit parameterized IonQ gates
    if cirq_ionq_ops and isinstance(gate, (braket_gates.GPi, braket_gates.GPi2)):
        phi = gate.angle / (2 * np.pi)
        gate_class = (
            cirq_ionq_ops.GPIGate if isinstance(gate, braket_gates.GPi) else cirq_ionq_ops.GPI2Gate
        )
        return [gate_class(phi=phi).on(*qubits)]

    # One-qubit Noise gates.
    if isinstance(gate, braket_noise_gate.BitFlip):
        return [cirq_ops.BitFlipChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.PhaseFlip):
        return [cirq_ops.PhaseFlipChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.Depolarizing):
        return [cirq_ops.DepolarizingChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.AmplitudeDamping):
        return [cirq_ops.AmplitudeDampingChannel(gate.gamma).on(*qubits)]
    if isinstance(gate, braket_noise_gate.GeneralizedAmplitudeDamping):
        return [
            cirq_ops.GeneralizedAmplitudeDampingChannel(gate.probability, gate.gamma).on(*qubits)
        ]
    if isinstance(gate, braket_noise_gate.PhaseDamping):
        return [cirq_ops.PhaseDampingChannel(gate.gamma).on(*qubits)]

    try:
        matrix = _gate_to_matrix_braket(gate)
        return [cirq_ops.MatrixGate(matrix).on(*qubits)]
    except (ValueError, TypeError) as err:
        raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err


def _from_two_qubit_braket_instruction(
    instr: BKInstruction, qubits: List[LineQubit]
) -> List[cirq_ops.Operation]:
    """Converts the two-qubit braket instruction to Cirq.

    Args:
        instr: Two-qubit Braket instruction to convert.
        qubits: Cirq LineQubit list indexed according to Braket instruction

    Raises:
        ValueError: If the instruction cannot be converted to Cirq.
    """
    gate = instr.operator

    # Two-qubit non-parameterized gates.
    if isinstance(gate, braket_gates.CNot):
        return [cirq_ops.CNOT.on(*qubits)]

    if isinstance(gate, braket_gates.Swap):
        return [cirq_ops.SWAP.on(*qubits)]
    if isinstance(gate, braket_gates.ISwap):
        return [cirq_ops.ISWAP.on(*qubits)]
    if isinstance(gate, braket_gates.CZ):
        return [cirq_ops.CZ.on(*qubits)]
    if isinstance(gate, braket_gates.CY):
        return [
            protocols.inverse(cirq_ops.S.on(qubits[1])),
            cirq_ops.CNOT.on(*qubits),
            cirq_ops.S.on(qubits[1]),
        ]

    # Two-qubit parameterized gates.
    if isinstance(gate, braket_gates.CPhaseShift):
        return [cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi)]
    if isinstance(gate, braket_gates.CPhaseShift00):
        return [
            cirq_ops.XX(*qubits),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.XX(*qubits),
        ]
    if isinstance(gate, braket_gates.CPhaseShift01):
        return [
            cirq_ops.X(qubits[0]),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.X(qubits[0]),
        ]
    if isinstance(gate, braket_gates.CPhaseShift10):
        return [
            cirq_ops.X(qubits[1]),
            cirq_ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq_ops.X(qubits[1]),
        ]
    if isinstance(gate, braket_gates.PSwap):
        return [
            cirq_ops.SWAP.on(*qubits),
            cirq_ops.CNOT.on(*qubits),
            cirq_ops.Z.on(qubits[1]) ** (gate.angle / np.pi),
            cirq_ops.CNOT.on(*qubits),
        ]
    if isinstance(gate, braket_gates.XX):
        return [cirq_ops.XXPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.YY):
        return [cirq_ops.YYPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.ZZ):
        return [cirq_ops.ZZPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.XY):
        return [cirq_ops.ISwapPowGate(exponent=gate.angle / np.pi).on(*qubits)]

    # Two-qubit noise gates.
    if isinstance(gate, braket_noise_gate.Kraus):
        return [cirq_ops.KrausChannel(gate._matrices).on(*qubits)]
    if isinstance(gate, braket_noise_gate.TwoQubitDepolarizing):
        return [cirq_ops.DepolarizingChannel(gate.probability, n_qubits=2).on(*qubits)]

    # Two-qubit two-parameters IonQ gates.
    if cirq_ionq_ops and isinstance(gate, braket_gates.MS):
        return [
            cirq_ionq_ops.MSGate(
                phi0=gate.angle_1 / (2 * np.pi),
                phi1=gate.angle_2 / (2 * np.pi),
                theta=gate.angle_3 / (2 * np.pi),
            ).on(*qubits)
        ]

    try:
        matrix = _gate_to_matrix_braket(gate)
        unitary_gate = matrix_gate(matrix)
        return [unitary_gate.on(*qubits)]
    except (ValueError, TypeError) as err:
        raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err
