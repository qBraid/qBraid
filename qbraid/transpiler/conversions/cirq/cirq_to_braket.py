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

from copy import deepcopy
from typing import TYPE_CHECKING, Optional, Union

import numpy as np

try:
    from braket.circuits import Circuit as BKCircuit
    from braket.circuits import Instruction as BKInstruction
    from braket.circuits import gates as braket_gates
    from braket.circuits import noises as braket_noise_gate
except ImportError:  # pragma: no cover
    BKCircuit = None
    BKInstruction = None
    braket_gates = None
    braket_noise_gate = None

from cirq import Circuit
from cirq import ops as cirq_ops
from cirq import protocols
from cirq.linalg.decompositions import kak_decomposition

try:
    import cirq_ionq.ionq_native_gates as cirq_ionq_ops
except ImportError:  # pragma: no cover
    cirq_ionq_ops = None

import qbraid.programs.gate_model.cirq
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import CircuitConversionError

try:
    from .braket_custom import C as BKControl
except ImportError:  # pragma: no cover
    BKControl = None

if TYPE_CHECKING:
    import braket.circuits


@weight(0.85)
def cirq_to_braket(circuit: Circuit) -> braket.circuits.Circuit:
    """Returns a Braket circuit equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Braket circuit.

    Returns:
        Braket circuit equivalent to the input Cirq circuit.
    """
    cirq_qubits = list(circuit.all_qubits())
    cirq_int_qubits = [
        qbraid.programs.gate_model.cirq.CirqCircuit._int_from_qubit(q) for q in cirq_qubits
    ]
    braket_int_qubits = deepcopy(cirq_int_qubits)
    qubit_mapping = {q: braket_int_qubits[i] for i, q in enumerate(cirq_int_qubits)}
    return BKCircuit(
        _to_braket_instruction(operation, qubit_mapping) for operation in circuit.all_operations()
    )


def _to_braket_instruction(
    operation: cirq_ops.Operation,
    qubit_mapping: dict[int, int],
) -> list[braket.circuits.Instruction]:
    """Converts Cirq operation to equivalent Braket instruction(s).

    Args:
        operation: Cirq operation to convert.
        qubit_mapping: Mappings of input / output qubit indicies

    Raises:
        CircuitConversionError: If the operation cannot be converted to Braket.
    """
    if isinstance(
        operation, (cirq_ops.MeasurementGate, cirq_ops.Operation)
    ) and qbraid.programs.gate_model.cirq.CirqCircuit.is_measurement_gate(operation):
        return []

    nqubits = protocols.num_qubits(operation)
    cirq_qubits = operation.qubits
    cirq_qubits = [
        qbraid.programs.gate_model.cirq.CirqCircuit._int_from_qubit(q) for q in operation.qubits
    ]
    qubits = [qubit_mapping[x] for x in cirq_qubits]

    if nqubits == 1:
        target = qubits[0]
        return _to_one_qubit_braket_instruction(operation, target)

    if nqubits == 2:
        return _to_two_qubit_braket_instruction(operation, qubits)

    if nqubits == 3:
        if operation == cirq_ops.TOFFOLI.on(*operation.qubits):
            return [BKInstruction(braket_gates.CCNot(), qubits)]
        if operation == cirq_ops.FREDKIN.on(*operation.qubits):
            return [BKInstruction(braket_gates.CSwap(), qubits)]
        if isinstance(operation.gate, cirq_ops.ControlledGate):
            sub_gate_instr = _to_two_qubit_braket_instruction(operation.gate.sub_gate, qubits[1:])
            sub_gate = sub_gate_instr[0].operator
            # return [BKInstruction(sub_gate, target=qubits[1:], control=qubits[:1])]
            return [BKInstruction(BKControl(sub_gate, qubits), qubits)]

        try:
            matrix = protocols.unitary(operation)
            name = str(operation.gate)
            return [
                BKInstruction(
                    braket_gates.Unitary(matrix, display_name=name),
                    qubits,
                )
            ]
        except (ValueError, TypeError) as err:
            raise CircuitConversionError(f"Unable to convert {operation} to Braket") from err

    # Unsupported gates.
    raise CircuitConversionError(f"Unable to convert {operation} to Braket")


def _to_one_qubit_braket_instruction(
    operation: Union[np.ndarray, cirq_ops.Gate, cirq_ops.Operation],
    target: int,
    gate_name: Optional[str] = None,
) -> list[braket.circuits.Instruction]:
    """Converts one-qubit Cirq operation or NumPy array to equivalent Braket instruction(s)

    Args:
        operation: One-qubit Cirq operation or numpy unitary to translate.
        target: Qubit index for the operation to act on. Must be specified and if only
            if `operation` is given as a numpy array.
        gate_name: Optional unitary gate display name for `operation` of type `np.ndarray`

    Raises:
        ValueError: If the operation cannot be converted to Braket.
    """

    def instruction_from_matrix(matrix, target, name):
        display_name = "U" if name is None or "QasmUGate" in name else name
        return [BKInstruction(braket_gates.Unitary(matrix, display_name=display_name), target)]

    def convert_one_qubit_gate(gate, target):
        if isinstance(gate, cirq_ops.XPowGate):
            exponent = gate.exponent
            if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
                return [BKInstruction(braket_gates.X(), target)]
            if np.isclose(exponent, 0.5):
                return [BKInstruction(braket_gates.V(), target)]
            if np.isclose(exponent, -0.5):
                return [BKInstruction(braket_gates.Vi(), target)]

            return [BKInstruction(braket_gates.Rx(exponent * np.pi), target)]

        if isinstance(gate, cirq_ops.YPowGate):
            exponent = gate.exponent

            if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
                return [BKInstruction(braket_gates.Y(), target)]

            return [BKInstruction(braket_gates.Ry(exponent * np.pi), target)]

        if isinstance(gate, cirq_ops.ZPowGate):
            global_shift = gate.global_shift
            exponent = gate.exponent

            if np.isclose(global_shift, 0.0):
                if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
                    return [BKInstruction(braket_gates.Z(), target)]
                if np.isclose(exponent, 0.5):
                    return [BKInstruction(braket_gates.S(), target)]
                if np.isclose(exponent, -0.5):
                    return [BKInstruction(braket_gates.Si(), target)]
                if np.isclose(exponent, 0.25):
                    return [BKInstruction(braket_gates.T(), target)]
                if np.isclose(exponent, -0.25):
                    return [BKInstruction(braket_gates.Ti(), target)]
                return [BKInstruction(braket_gates.PhaseShift(exponent * np.pi), target)]
            if np.isclose(global_shift, -0.5):
                return [BKInstruction(braket_gates.Rz(exponent * np.pi), target)]

        if isinstance(gate, cirq_ops.HPowGate) and np.isclose(abs(gate.exponent), 1.0):
            return [BKInstruction(braket_gates.H(), target)]

        if isinstance(gate, cirq_ops.IdentityGate):
            return [BKInstruction(braket_gates.I(), target)]

        if isinstance(gate, cirq_ops.BitFlipChannel):
            return [BKInstruction(braket_noise_gate.BitFlip(operation.gate._p), target)]

        if isinstance(gate, cirq_ops.PhaseFlipChannel):
            return [BKInstruction(braket_noise_gate.PhaseFlip(operation.gate._p), target)]

        if isinstance(gate, cirq_ops.DepolarizingChannel):
            return [BKInstruction(braket_noise_gate.Depolarizing(operation.gate._p), target)]

        if isinstance(gate, cirq_ops.AmplitudeDampingChannel):
            return [
                BKInstruction(braket_noise_gate.AmplitudeDamping(operation.gate._gamma), target)
            ]

        if isinstance(gate, cirq_ops.GeneralizedAmplitudeDampingChannel):
            return [
                BKInstruction(
                    braket_noise_gate.GeneralizedAmplitudeDamping(
                        gamma=operation.gate._gamma, probability=operation.gate._p
                    ),
                    target,
                )
            ]

        if isinstance(gate, cirq_ops.PhaseDampingChannel):
            return [BKInstruction(braket_noise_gate.PhaseDamping(operation.gate._gamma), target)]

        if cirq_ionq_ops and isinstance(
            gate, (cirq_ionq_ops.GPIGate, cirq_ionq_ops.GPI2Gate, cirq_ionq_ops.MSGate)
        ):
            if isinstance(gate, cirq_ionq_ops.GPIGate):
                return [
                    BKInstruction(braket_gates.GPi(angle=operation.gate.phi * 2 * np.pi), target)
                ]
            if isinstance(gate, cirq_ionq_ops.GPI2Gate):
                return [
                    BKInstruction(braket_gates.GPi2(angle=operation.gate.phi * 2 * np.pi), target)
                ]

        matrix = protocols.unitary(gate)
        gate_name = "U" if isinstance(gate, cirq_ops.MatrixGate) else str(gate)
        return _to_one_qubit_braket_instruction(matrix, target, gate_name=gate_name)

    if isinstance(operation, np.ndarray):
        return instruction_from_matrix(operation, target, gate_name)

    if isinstance(operation, cirq_ops.Operation):
        gate = operation.gate
    elif isinstance(operation, cirq_ops.Gate):
        gate = operation
    else:
        raise ValueError(f"Unable to convert {operation} to braket")

    return convert_one_qubit_gate(gate, target)


def _to_two_qubit_braket_instruction(
    operation: Union[cirq_ops.Gate, cirq_ops.Operation],
    qubits: list[int],
) -> list[braket.circuits.Instruction]:
    """Converts two-qubit Cirq operation to equivalent Braket instruction(s)

    Args:
        operation: Two-qubit Cirq operation to translate.
        qubits: Length 2 list of qubit indicies

    Raises:
        ValueError: If the operation cannot be converted to Braket.
    """
    if isinstance(operation, cirq_ops.Operation):
        gate = operation.gate

    elif isinstance(operation, cirq_ops.Gate):
        gate = operation

    else:
        raise ValueError(f"Unable to convert {operation} to Braket")

    # Translate qubit indices.
    q1, q2 = qubits

    # Check common two-qubit gates.
    if isinstance(gate, cirq_ops.CNotPowGate) and np.isclose(abs(gate.exponent), 1.0):
        return [BKInstruction(braket_gates.CNot(), [q1, q2])]
    if isinstance(gate, cirq_ops.CZPowGate) and np.isclose(abs(gate.exponent), 1.0):
        return [BKInstruction(braket_gates.CZ(), [q1, q2])]
    if isinstance(gate, cirq_ops.SwapPowGate) and np.isclose(gate.exponent, 1.0):
        return [BKInstruction(braket_gates.Swap(), [q1, q2])]
    if isinstance(gate, cirq_ops.ISwapPowGate) and np.isclose(gate.exponent, 1.0):
        return [BKInstruction(braket_gates.ISwap(), [q1, q2])]
    if isinstance(gate, cirq_ops.XXPowGate):
        return [BKInstruction(braket_gates.XX(gate.exponent * np.pi), [q1, q2])]
    if isinstance(gate, cirq_ops.YYPowGate):
        return [BKInstruction(braket_gates.YY(gate.exponent * np.pi), [q1, q2])]
    if isinstance(gate, cirq_ops.ZZPowGate):
        return [BKInstruction(braket_gates.ZZ(gate.exponent * np.pi), [q1, q2])]
    if isinstance(gate, cirq_ops.ControlledGate):
        sub_gate_instr = _to_one_qubit_braket_instruction(gate.sub_gate, q2)
        sub_gate = sub_gate_instr[0].operator
        # return [BKInstruction(sub_gate, target=q2, control=q1)]
        return [BKInstruction(BKControl(sub_gate, [0, 1]), [q1, q2])]
    if isinstance(gate, cirq_ops.DepolarizingChannel):
        return BKInstruction(braket_noise_gate.TwoQubitDepolarizing(operation.gate.p), [q1, q2])
    if isinstance(gate, cirq_ops.KrausChannel):
        return BKInstruction(braket_noise_gate.Kraus(matrices=operation.gate._kraus_ops), [q1, q2])
    if isinstance(gate, cirq_ionq_ops.MSGate):
        return [
            BKInstruction(
                braket_gates.MS(
                    angle_1=operation.gate.phi0 * 2 * np.pi,
                    angle_2=operation.gate.phi1 * 2 * np.pi,
                    angle_3=operation.gate.theta * 2 * np.pi,
                ),
                [q1, q2],
            )
        ]

    # Fallback: arbitrary two-qubit unitary (KAK) decomposition
    unitary = protocols.unitary(operation)
    return _kak_decomposition_to_braket_instruction(unitary, q1, q2)


def _kak_decomposition_to_braket_instruction(
    matrix: np.ndarray, q1: int, q2: int
) -> list[braket.circuits.Instruction]:
    """Converts 4x4 Numpy array to equivalent Braket instruction(s) via kak decomposition

    Args:
        matrix: Unitary 4x4 numpy array representing 2-qubit gate.
        q1: Index of first qubit to act on
        q2: Index of second qubit to act on
    """
    kak = kak_decomposition(matrix)
    A1, A2 = kak.single_qubit_operations_before

    x, y, z = kak.interaction_coefficients
    a = x * -2 / np.pi + 0.5
    b = y * -2 / np.pi + 0.5
    c = z * -2 / np.pi + 0.5

    B1, B2 = kak.single_qubit_operations_after

    return [
        *_to_one_qubit_braket_instruction(A1, q1),
        *_to_one_qubit_braket_instruction(A2, q2),
        BKInstruction(braket_gates.Rx(0.5 * np.pi), q1),
        BKInstruction(braket_gates.CNot(), [q1, q2]),
        BKInstruction(braket_gates.Rx(a * np.pi), q1),
        BKInstruction(braket_gates.Ry(b * np.pi), q2),
        BKInstruction(braket_gates.CNot(), [q2, q1]),
        BKInstruction(braket_gates.Rx(-0.5 * np.pi), q2),
        BKInstruction(braket_gates.Rz(c * np.pi), q2),
        BKInstruction(braket_gates.CNot(), [q1, q2]),
        *_to_one_qubit_braket_instruction(B1, q1),
        *_to_one_qubit_braket_instruction(B2, q2),
    ]
