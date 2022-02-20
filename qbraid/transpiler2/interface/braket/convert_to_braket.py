# Copyright (C) 2021 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from typing import Any, Dict, List, Union

import numpy as np

from cirq import Circuit, ops as cirq_ops, protocols
from cirq.linalg.decompositions import kak_decomposition
from braket.circuits import (
    gates as braket_gates,
    Circuit as BKCircuit,
    Instruction as BKInstruction,
)
from qbraid.transpiler2.utils import _int_from_qubit, _contiguous_compression_cirq
from qbraid.transpiler2.interface.braket.braket_utils import C as BKControl


def _raise_cirq_to_braket_error(op: Any) -> None:
    raise ValueError(f"Unable to convert {op} to Braket.")


def to_braket(circuit: Circuit) -> BKCircuit:
    """Returns a Braket circuit equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Braket circuit.
    """
    compat_circuit = _contiguous_compression_cirq(circuit)
    cirq_int_qubits = range(len(compat_circuit.all_qubits()))
    braket_int_qubits = list(reversed(cirq_int_qubits))
    qubit_mapping = {
        x: braket_int_qubits[x] for x in range(len(braket_int_qubits))
    }
    return BKCircuit(
        _translate_cirq_operation_to_braket_instruction(op, qubit_mapping)
        for op in compat_circuit.all_operations()
    )


def _translate_cirq_operation_to_braket_instruction(
    op: cirq_ops.Operation,
    qubit_mapping: Dict[int, int],
) -> List[BKInstruction]:
    """Converts the Cirq operation to an equivalent Braket instruction or list
    of instructions.

    Args:
        op: Cirq operation to convert.

    Raises:
        ValueError: If the operation cannot be converted to Braket.
    """
    nqubits = protocols.num_qubits(op)
    cirq_qubits = [_int_from_qubit(q) for q in op.qubits]
    qubits = [qubit_mapping[x] for x in cirq_qubits]

    if nqubits == 1:
        target = qubits[0]
        return _translate_one_qubit_cirq_operation_to_braket_instruction(
            op, target
        )

    elif nqubits == 2:
        return _translate_two_qubit_cirq_operation_to_braket_instruction(
            op, qubits
        )

    elif nqubits == 3:
        if op == cirq_ops.TOFFOLI.on(*op.qubits):
            return [BKInstruction(braket_gates.CCNot(), qubits)]
        elif op == cirq_ops.FREDKIN.on(*op.qubits):
            return [BKInstruction(braket_gates.CSwap(), qubits)]
        elif isinstance(op.gate, cirq_ops.ControlledGate):
            sub_gate_instr = (
                _translate_two_qubit_cirq_operation_to_braket_instruction(
                    op.gate.sub_gate, qubits[1:]
                )
            )
            sub_gate = sub_gate_instr[0].operator
            return [BKInstruction(BKControl(sub_gate, qubits), qubits)]
        else:
            try:
                matrix = protocols.unitary(op)
                name = str(op.gate)
                return [
                    BKInstruction(
                        braket_gates.Unitary(matrix, display_name=name),
                        qubits,
                    )
                ]
            except (ValueError, TypeError):
                _raise_cirq_to_braket_error(op)

    # Unsupported gates.
    else:
        _raise_cirq_to_braket_error(op)

    return None  # type: ignore[return-value]  # pragma: no cover


def _translate_one_qubit_cirq_operation_to_braket_instruction(
    op: Union[np.ndarray, cirq_ops.Gate, cirq_ops.Operation],
    target: int,
    name: str = None,
) -> List[BKInstruction]:
    """Translates a one-qubit Cirq operation to a (sequence of) Braket
    instruction(s) according to the following rules:

    1. Attempts to find a "standard translation" from Cirq to Braket.
        - e.g., checks if `op` is Pauli-X and, if so, returns the Braket X.

    2. If (1) is not successful, decomposes the unitary of `op` to
    Rz(theta) Ry(phi) Rz(lambda) and returns the series of rotations as Braket
    instructions.

    Args:
        op: One-qubit Cirq operation to translate.
        target: Qubit index for the op to act on. Must be specified and if only
            if `op` is given as a numpy array.
        name: Optional unitary gate display name for `op` of type `np.ndarray`
    """
    if isinstance(op, np.ndarray):
        gate_name = "U" if name is None else name
        return [
            BKInstruction(
                braket_gates.Unitary(op, display_name=gate_name), target
            )
        ]

    # Check common single-qubit gates.
    elif isinstance(op, cirq_ops.Operation):
        gate = op.gate

    elif isinstance(op, cirq_ops.Gate):
        gate = op

    else:
        raise _raise_cirq_to_braket_error(op)

    if isinstance(gate, cirq_ops.XPowGate):
        exponent = gate.exponent
        if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
            return [BKInstruction(braket_gates.X(), target)]
        elif np.isclose(exponent, 0.5):
            return [BKInstruction(braket_gates.V(), target)]
        elif np.isclose(exponent, -0.5):
            return [BKInstruction(braket_gates.Vi(), target)]

        return [BKInstruction(braket_gates.Rx(exponent * np.pi), target)]

    elif isinstance(gate, cirq_ops.YPowGate):
        exponent = gate.exponent

        if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
            return [BKInstruction(braket_gates.Y(), target)]

        return [BKInstruction(braket_gates.Ry(exponent * np.pi), target)]

    elif isinstance(gate, cirq_ops.ZPowGate):
        global_shift = gate.global_shift
        exponent = gate.exponent

        if np.isclose(global_shift, 0.0):
            if np.isclose(exponent, 1.0) or np.isclose(exponent, -1.0):
                return [BKInstruction(braket_gates.Z(), target)]
            elif np.isclose(exponent, 0.5):
                return [BKInstruction(braket_gates.S(), target)]
            elif np.isclose(exponent, -0.5):
                return [BKInstruction(braket_gates.Si(), target)]
            elif np.isclose(exponent, 0.25):
                return [BKInstruction(braket_gates.T(), target)]
            elif np.isclose(exponent, -0.25):
                return [BKInstruction(braket_gates.Ti(), target)]
            else:
                return [
                    BKInstruction(
                        braket_gates.PhaseShift(exponent * np.pi), target
                    )
                ]
        if np.isclose(global_shift, -0.5):
            return [BKInstruction(braket_gates.Rz(exponent * np.pi), target)]

    elif isinstance(gate, cirq_ops.HPowGate) and np.isclose(
        abs(gate.exponent), 1.0
    ):
        return [BKInstruction(braket_gates.H(), target)]

    elif isinstance(gate, cirq_ops.IdentityGate):
        return [BKInstruction(braket_gates.I(), target)]

    else:
        matrix = protocols.unitary(gate)
        return _translate_one_qubit_cirq_operation_to_braket_instruction(
            matrix, target, name=str(gate)
        )


def _translate_two_qubit_cirq_operation_to_braket_instruction(
    op: Union[cirq_ops.Gate, cirq_ops.Operation],
    qubits: List[int],
) -> List[BKInstruction]:
    """Translates a two-qubit Cirq operation to a (sequence of) Braket
    instruction(s) according to the following rules:

    1. Attempts to find a "standard translation" from Cirq to Braket.
        - e.g., checks if `op` is a CNOT and, if so, returns the Braket CNOT.

    2. If (1) is not successful, performs a KAK decomposition of the unitary of
    `op` to obtain a circuit

        ──A1──X^0.5───@───X^a───X──────────────────@───B1───
                      │         │                  │
        ──A2──────────X───Y^b───@───X^-0.5───Z^c───X───B2────

    where A1, A2, B1, and B2 are arbitrary single-qubit unitaries and a, b, c
    are floats.

    Args:
        op: Two-qubit Cirq operation to translate.
    """
    # Translate qubit indices.
    q1, q2 = qubits

    # Check common single-qubit gates.
    if isinstance(op, cirq_ops.Operation):
        gate = op.gate

    elif isinstance(op, cirq_ops.Gate):
        gate = op

    else:
        raise _raise_cirq_to_braket_error(op)

    # Check common two-qubit gates.
    if isinstance(gate, cirq_ops.CNotPowGate) and np.isclose(
        abs(gate.exponent), 1.0
    ):
        return [BKInstruction(braket_gates.CNot(), [q1, q2])]
    elif isinstance(gate, cirq_ops.CZPowGate) and np.isclose(
        abs(gate.exponent), 1.0
    ):
        return [BKInstruction(braket_gates.CZ(), [q1, q2])]
    elif isinstance(gate, cirq_ops.SwapPowGate) and np.isclose(
        gate.exponent, 1.0
    ):
        return [BKInstruction(braket_gates.Swap(), [q1, q2])]
    elif isinstance(gate, cirq_ops.ISwapPowGate) and np.isclose(
        gate.exponent, 1.0
    ):
        return [BKInstruction(braket_gates.ISwap(), [q1, q2])]
    elif isinstance(gate, cirq_ops.XXPowGate):
        return [
            BKInstruction(braket_gates.XX(gate.exponent * np.pi), [q1, q2])
        ]
    elif isinstance(gate, cirq_ops.YYPowGate):
        return [
            BKInstruction(braket_gates.YY(gate.exponent * np.pi), [q1, q2])
        ]
    elif isinstance(gate, cirq_ops.ZZPowGate):
        return [
            BKInstruction(braket_gates.ZZ(gate.exponent * np.pi), [q1, q2])
        ]
    elif isinstance(gate, cirq_ops.ControlledGate):
        sub_gate_instr = (
            _translate_one_qubit_cirq_operation_to_braket_instruction(
                gate.sub_gate, q2
            )
        )
        sub_gate = sub_gate_instr[0].operator
        return [BKInstruction(BKControl(sub_gate, [0, 1]), [q1, q2])]

    # Arbitrary two-qubit unitary decomposition.
    kak = kak_decomposition(protocols.unitary(op))
    A1, A2 = kak.single_qubit_operations_before

    x, y, z = kak.interaction_coefficients
    a = x * -2 / np.pi + 0.5
    b = y * -2 / np.pi + 0.5
    c = z * -2 / np.pi + 0.5

    B1, B2 = kak.single_qubit_operations_after

    return [
        *_translate_one_qubit_cirq_operation_to_braket_instruction(A1, q1),
        *_translate_one_qubit_cirq_operation_to_braket_instruction(A2, q2),
        BKInstruction(braket_gates.Rx(0.5 * np.pi), q1),
        BKInstruction(braket_gates.CNot(), [q1, q2]),
        BKInstruction(braket_gates.Rx(a * np.pi), q1),
        BKInstruction(braket_gates.Ry(b * np.pi), q2),
        BKInstruction(braket_gates.CNot(), [q2, q1]),
        BKInstruction(braket_gates.Rx(-0.5 * np.pi), q2),
        BKInstruction(braket_gates.Rz(c * np.pi), q2),
        BKInstruction(braket_gates.CNot(), [q1, q2]),
        *_translate_one_qubit_cirq_operation_to_braket_instruction(B1, q1),
        *_translate_one_qubit_cirq_operation_to_braket_instruction(B2, q2),
    ]
