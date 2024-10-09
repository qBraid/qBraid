# Copyright (C) 2024 qBraid
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

# qbraid: skip-header

"""
Module for converting Braket circuits to Cirq circuits

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction as BKInstruction
from braket.circuits import gates as braket_gates
from braket.circuits import noises as braket_noise_gate

try:
    import cirq
except ImportError:  # pragma: no cover
    cirq = None

try:
    import cirq_ionq.ionq_native_gates as cirq_ionq_ops
except ImportError:  # pragma: no cover
    cirq_ionq_ops = None

from qbraid.programs.gate_model.cirq import CirqCircuit as QbraidCircuit
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import cirq.circuits as cirq_circuits
    import cirq.devices as cirq_devices
    import cirq.ops as cirq_ops


def _give_cirq_gate_name(gate: cirq_ops.Gate, name: str, n_qubits: int) -> cirq_ops.Gate:
    def _circuit_diagram_info_(args):  # pylint: disable=unused-argument
        return name, *(name,) * (n_qubits - 1)

    gate._circuit_diagram_info_ = _circuit_diagram_info_


def matrix_to_cirq_gate(matrix: np.ndarray) -> cirq_ops.MatrixGate:
    """Return cirq matrix gate given unitary"""
    n_qubits = int(np.log2(len(matrix)))
    unitary_gate = cirq.MatrixGate(matrix)
    _give_cirq_gate_name(unitary_gate, "U", n_qubits)
    return unitary_gate


def braket_gate_to_matrix(gate: braket_gates.Unitary) -> np.ndarray:
    """Return the matrix representation of a Braket gate."""
    matrix = gate.to_matrix()
    unitary_gate = braket_gates.Unitary(matrix)
    nqubits = int(np.log2(len(matrix)))
    qubits = list(range(nqubits)) if nqubits > 1 else 0
    bk_circuit = BKCircuit([BKInstruction(unitary_gate, qubits)])
    return bk_circuit.to_unitary()


@weight(1)
def braket_to_cirq(circuit: BKCircuit) -> cirq_circuits.Circuit:
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit equivalent to the input Braket circuit.
    """
    bk_qubits = [int(q) for q in circuit.qubits]
    cirq_qubits = [cirq.LineQubit(x) for x in bk_qubits]
    qubit_mapping = {q: cirq_qubits[i] for i, q in enumerate(bk_qubits)}
    circuit = cirq.Circuit(
        _from_braket_instruction(instr, qubit_mapping) for instr in circuit.instructions
    )
    return QbraidCircuit.align_final_measurements(circuit)


def _from_braket_instruction(
    instr: BKInstruction, qubit_mapping: dict[int, cirq_devices.LineQubit]
) -> list[cirq_ops.Operation]:
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

    if str(instr.operator) == "Measure":
        return [cirq.ops.MeasurementGate(num_qubits=nqubits).on(*qubits)]

    try:
        if nqubits == 1:
            return _from_one_qubit_braket_instruction(instr, qubits)

        if nqubits == 2:
            return _from_two_qubit_braket_instruction(instr, qubits)

        if nqubits == 3:
            if isinstance(instr.operator, braket_gates.CCNot):
                return [cirq.ops.TOFFOLI.on(*qubits)]
            if isinstance(instr.operator, braket_gates.CSwap):
                return [cirq.ops.FREDKIN.on(*qubits)]
            try:
                matrix = braket_gate_to_matrix(instr.operator)
                return [cirq.ops.MatrixGate(matrix).on(*qubits)]
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
    instr: BKInstruction, qubits: list[cirq_devices.LineQubit]
) -> list[cirq_ops.Operation]:
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
        return [cirq.ops.I.on(*qubits)]
    if isinstance(gate, braket_gates.X):
        return [cirq.ops.X.on(*qubits)]
    if isinstance(gate, braket_gates.Y):
        return [cirq.ops.Y.on(*qubits)]
    if isinstance(gate, braket_gates.Z):
        return [cirq.ops.Z.on(*qubits)]
    if isinstance(gate, braket_gates.H):
        return [cirq.ops.H.on(*qubits)]
    if isinstance(gate, braket_gates.S):
        return [cirq.ops.S.on(*qubits)]
    if isinstance(gate, braket_gates.Si):
        return [cirq.protocols.inverse(cirq.ops.S.on(*qubits))]
    if isinstance(gate, braket_gates.T):
        return [cirq.ops.T.on(*qubits)]
    if isinstance(gate, braket_gates.Ti):
        return [cirq.protocols.inverse(cirq.ops.T.on(*qubits))]
    if isinstance(gate, braket_gates.V):
        return [cirq.ops.X.on(*qubits) ** 0.5]
    if isinstance(gate, braket_gates.Vi):
        return [cirq.ops.X.on(*qubits) ** -0.5]

    # One-qubit parameterized gates.
    if isinstance(gate, braket_gates.Rx):
        return [cirq.ops.rx(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.Ry):
        return [cirq.ops.ry(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.Rz):
        return [cirq.ops.rz(gate.angle).on(*qubits)]
    if isinstance(gate, braket_gates.PhaseShift):
        return [cirq.ops.Z.on(*qubits) ** (gate.angle / np.pi)]

    # One-qubit parameterized IonQ gates
    if cirq_ionq_ops and isinstance(gate, (braket_gates.GPi, braket_gates.GPi2)):
        phi = gate.angle / (2 * np.pi)
        gate_class = (
            cirq_ionq_ops.GPIGate if isinstance(gate, braket_gates.GPi) else cirq_ionq_ops.GPI2Gate
        )
        return [gate_class(phi=phi).on(*qubits)]

    # One-qubit Noise gates.
    if isinstance(gate, braket_noise_gate.BitFlip):
        return [cirq.ops.BitFlipChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.PhaseFlip):
        return [cirq.ops.PhaseFlipChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.Depolarizing):
        return [cirq.ops.DepolarizingChannel(gate.probability).on(*qubits)]
    if isinstance(gate, braket_noise_gate.AmplitudeDamping):
        return [cirq.ops.AmplitudeDampingChannel(gate.gamma).on(*qubits)]
    if isinstance(gate, braket_noise_gate.GeneralizedAmplitudeDamping):
        return [
            cirq.ops.GeneralizedAmplitudeDampingChannel(gate.probability, gate.gamma).on(*qubits)
        ]
    if isinstance(gate, braket_noise_gate.PhaseDamping):
        return [cirq.ops.PhaseDampingChannel(gate.gamma).on(*qubits)]

    try:
        matrix = braket_gate_to_matrix(gate)
        return [cirq.ops.MatrixGate(matrix).on(*qubits)]
    except (ValueError, TypeError) as err:
        raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err


def _from_two_qubit_braket_instruction(
    instr: BKInstruction, qubits: list[cirq_devices.LineQubit]
) -> list[cirq_ops.Operation]:
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
        return [cirq.ops.CNOT.on(*qubits)]

    if isinstance(gate, braket_gates.Swap):
        return [cirq.ops.SWAP.on(*qubits)]
    if isinstance(gate, braket_gates.ISwap):
        return [cirq.ops.ISWAP.on(*qubits)]
    if isinstance(gate, braket_gates.CZ):
        return [cirq.ops.CZ.on(*qubits)]
    if isinstance(gate, braket_gates.CY):
        return [
            cirq.protocols.inverse(cirq.ops.S.on(qubits[1])),
            cirq.ops.CNOT.on(*qubits),
            cirq.ops.S.on(qubits[1]),
        ]

    # Two-qubit parameterized gates.
    if isinstance(gate, braket_gates.CPhaseShift):
        return [cirq.ops.CZ.on(*qubits) ** (gate.angle / np.pi)]
    if isinstance(gate, braket_gates.CPhaseShift00):
        return [
            cirq.ops.XX(*qubits),
            cirq.ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq.ops.XX(*qubits),
        ]
    if isinstance(gate, braket_gates.CPhaseShift01):
        return [
            cirq.ops.X(qubits[0]),
            cirq.ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq.ops.X(qubits[0]),
        ]
    if isinstance(gate, braket_gates.CPhaseShift10):
        return [
            cirq.ops.X(qubits[1]),
            cirq.ops.CZ.on(*qubits) ** (gate.angle / np.pi),
            cirq.ops.X(qubits[1]),
        ]
    if isinstance(gate, braket_gates.PSwap):
        return [
            cirq.ops.SWAP.on(*qubits),
            cirq.ops.CNOT.on(*qubits),
            cirq.ops.Z.on(qubits[1]) ** (gate.angle / np.pi),
            cirq.ops.CNOT.on(*qubits),
        ]
    if isinstance(gate, braket_gates.XX):
        return [cirq.ops.XXPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.YY):
        return [cirq.ops.YYPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.ZZ):
        return [cirq.ops.ZZPowGate(exponent=gate.angle / np.pi, global_shift=-0.5).on(*qubits)]
    if isinstance(gate, braket_gates.XY):
        return [cirq.ops.ISwapPowGate(exponent=gate.angle / np.pi).on(*qubits)]

    # Two-qubit noise gates.
    if isinstance(gate, braket_noise_gate.Kraus):
        return [cirq.ops.KrausChannel(gate._matrices).on(*qubits)]
    if isinstance(gate, braket_noise_gate.TwoQubitDepolarizing):
        return [cirq.ops.DepolarizingChannel(gate.probability, n_qubits=2).on(*qubits)]

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
        matrix = braket_gate_to_matrix(gate)
        unitary_gate = matrix_to_cirq_gate(matrix)
        return [unitary_gate.on(*qubits)]
    except (ValueError, TypeError) as err:
        raise ValueError(f"Unable to convert the instruction {instr} to Cirq.") from err
