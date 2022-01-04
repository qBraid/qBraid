# Copyright (C) 2020 Unitary Fund
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

"""Utility functions."""
from copy import deepcopy
from typing import cast, List, Tuple, Sequence, Union, TYPE_CHECKING

import numpy as np

from cirq import (
    LineQubit,
    GridQubit,
    NamedQubit,
    Circuit,
    CircuitDag,
    EigenGate,
    Gate,
    MatrixGate,
    GateOperation,
    Moment,
    I,
    ops,
)
from cirq.ops import Qid
from cirq.ops.measurement_gate import MeasurementGate


from qbraid.transpiler2.interface.cirq_qasm_gates import ZPowGate as QASM_ZPowGate

QUBIT = Union[LineQubit, GridQubit, NamedQubit, Qid]


def _simplify_gate_exponent(gate: EigenGate) -> EigenGate:
    """Returns the input gate with a simplified exponent if possible,
    otherwise the input gate is returned without any change.

    The input gate is not mutated.

    Args:
        gate: The input gate to simplify.

    Returns: The simplified gate.
    """
    # Try to simplify the gate exponent to 1
    if hasattr(gate, "_with_exponent") and gate == gate._with_exponent(1):
        return gate._with_exponent(1)
    return gate


def _simplify_circuit_exponents(circuit: Circuit) -> None:
    """Simplifies the gate exponents of the input circuit if possible,
    mutating the input circuit.

    Args:
        circuit: The circuit to simplify.
    """
    # Iterate over moments
    for moment_idx, moment in enumerate(circuit):
        simplified_operations = []
        # Iterate over operations in moment
        for op in moment:

            if not isinstance(op, GateOperation):
                simplified_operations.append(op)
                continue

            if isinstance(op.gate, EigenGate):
                simplified_gate: Gate = _simplify_gate_exponent(op.gate)
            else:
                simplified_gate = op.gate

            simplified_operation = op.with_gate(simplified_gate)
            simplified_operations.append(simplified_operation)
        # Mutate the input circuit
        circuit[moment_idx] = Moment(simplified_operations)


def _is_measurement(op: ops.Operation) -> bool:
    """Returns true if the operation's gate is a measurement, else False.

    Args:
        op: Gate operation.
    """
    return isinstance(op.gate, ops.measurement_gate.MeasurementGate)


def _pop_measurements(
    circuit: Circuit,
) -> List[Tuple[int, ops.Operation]]:
    """Removes all measurements from a circuit.

    Args:
        circuit: A quantum circuit as a :class:`cirq.Circuit` object.

    Returns:
        measurements: List of measurements in the circuit.
    """
    measurements = list(circuit.findall_operations(_is_measurement))
    circuit.batch_remove(measurements)
    return measurements


def _append_measurements(
    circuit: Circuit, measurements: List[Tuple[int, ops.Operation]]
) -> None:
    """Appends all measurements into the final moment of the circuit.

    Args:
        circuit: a quantum circuit as a :class:`cirq.Circuit`.
        measurements: measurements to perform.
    """
    new_measurements: List[Tuple[int, ops.Operation]] = []
    for i in range(len(measurements)):
        # Make sure the moment to insert into is the last in the circuit
        new_measurements.append((len(circuit) + 1, measurements[i][1]))
    circuit.batch_insert(new_measurements)


def _equal(
    circuit_one: Circuit,
    circuit_two: Circuit,
    require_qubit_equality: bool = False,
    require_measurement_equality: bool = False,
) -> bool:
    """Returns True if the circuits are equal, else False.

    Args:
        circuit_one: Input circuit to compare to circuit_two.
        circuit_two: Input circuit to compare to circuit_one.
        require_qubit_equality: Requires that the qubits be equal
            in the two circuits.
        require_measurement_equality: Requires that measurements are equal on
            the two circuits, meaning that measurement keys are equal.

    Note:
        If set(circuit_one.all_qubits()) = {LineQubit(0)},
        then set(circuit_two_all_qubits()) must be {LineQubit(0)},
        else the two are not equal.
        If True, the qubits of both circuits must have a well-defined ordering.
    """
    if circuit_one is circuit_two:
        return True

    circuit_one = deepcopy(circuit_one)
    circuit_two = deepcopy(circuit_two)

    if not require_qubit_equality:
        # Transform the qubits of circuit one to those of circuit two
        qubit_map = dict(
            zip(
                sorted(circuit_one.all_qubits()),
                sorted(circuit_two.all_qubits()),
            )
        )
        circuit_one = circuit_one.transform_qubits(lambda q: qubit_map[q])

    if not require_measurement_equality:
        for circ in (circuit_one, circuit_two):
            measurements = [
                (moment, op)
                for moment, op, _ in circ.findall_operations_with_gate_type(
                    MeasurementGate
                )
            ]
            circ.batch_remove(measurements)

            for i in range(len(measurements)):
                gate = cast(MeasurementGate, measurements[i][1].gate)
                gate.key = ""

            circ.batch_insert(measurements)

    return CircuitDag.from_circuit(circuit_one) == CircuitDag.from_circuit(
        circuit_two
    )


def _convert_to_line_qubits(
    circuit: Circuit,
    rev_qubits=False,
    qasm_zpow=False,
) -> Circuit:
    """Converts a Cirq circuit constructed using NamedQubits to
    a Cirq circuit constructed using LineQubits."""
    qubits = list(circuit.all_qubits())
    qubits.sort()
    if rev_qubits:
        qubits = list(reversed(qubits))
    qubit_map = {_key_from_qubit(q): i for i, q in enumerate(qubits)}
    line_qubit_circuit = Circuit()
    for op in circuit.all_operations():
        qubit_indicies = [qubit_map[_key_from_qubit(q)] for q in op.qubits]
        line_qubits = [LineQubit(i) for i in qubit_indicies]
        if qasm_zpow and isinstance(op.gate, ops.ZPowGate):
            if op.gate.global_shift != 0.0 and op.gate.global_shift != -0.5:
                coefficient = 1j ** (
                    2 * op.gate.exponent * op.gate.global_shift
                )
                matrix = coefficient * np.eye(2)
                qasm_zpowgate = QASM_ZPowGate(exponent=op.gate.exponent)
                matrix_gate = ops.MatrixGate(matrix)
                line_qubit_circuit.append(qasm_zpowgate.on(*line_qubits))
                line_qubit_circuit.append(matrix_gate.on(*line_qubits))
            else:
                qasm_zpowgate = QASM_ZPowGate(
                    exponent=op.gate.exponent,
                    global_shift=op.gate.global_shift,
                )
                line_qubit_circuit.append(qasm_zpowgate.on(*line_qubits))
        else:
            line_qubit_circuit.append(op.gate.on(*line_qubits))
    return line_qubit_circuit


def _key_from_qubit(qubit: Qid) -> str:
    if isinstance(qubit, LineQubit):
        key = str(qubit)
    elif isinstance(qubit, GridQubit):
        key = str(qubit.row)
    elif isinstance(qubit, NamedQubit):
        # Only correct if numbered sequentially
        key = str(qubit.name)
    else:
        raise ValueError(
            "Expected qubit of type 'GridQubit' or 'LineQubit'"
            f"but instead got {type(qubit)}"
        )
    return key


def _int_from_qubit(qubit: Qid) -> int:
    if isinstance(qubit, LineQubit):
        index = int(qubit)
    elif isinstance(qubit, GridQubit):
        index = qubit.row
    elif isinstance(qubit, NamedQubit):
        # Only correct if numbered sequentially
        index = int(qubit._comparison_key().split(":")[0][7:])
    else:
        raise ValueError(
            "Expected qubit of type 'GridQubit' or 'LineQubit'"
            f"but instead got {type(qubit)}"
        )
    return index


def _make_qubits(circuit: Circuit, qubits: List[int]) -> Sequence[Qid]:
    qubit_obj = list(circuit.all_qubits())[0]
    if isinstance(qubit_obj, LineQubit):
        qids = [LineQubit(i) for i in qubits]
    elif isinstance(qubit_obj, GridQubit):
        qids = [GridQubit(i, qubit_obj.col) for i in qubits]
    elif isinstance(qubit_obj, NamedQubit):
        qids = [NamedQubit(str(i)) for i in qubits]
    else:
        raise ValueError(
            "Expected qubits of type 'GridQubit', 'LineQubit', or "
            f"'NamedQubit' but instead got {type(qubit_obj)}"
        )
    return qids


def _convert_to_contiguous_cirq(circuit: Circuit) -> Circuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed."""
    nqubits = 0
    max_qubit = 0
    occupied_qubits = []
    cirq_qubits = list(circuit.all_qubits())
    if isinstance(cirq_qubits[0], NamedQubit):
        return _convert_to_line_qubits(circuit)
    for qubit in circuit.all_qubits():
        index = _int_from_qubit(qubit)
        occupied_qubits.append(index)
        if index > max_qubit:
            max_qubit = index
        nqubits += 1
    qubit_count = max_qubit + 1
    if qubit_count > nqubits:
        all_qubits = list(range(0, qubit_count))
        vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
        cirq_qubits = _make_qubits(circuit, vacant_qubits)
        for q in cirq_qubits:
            circuit.append(I(q))
    return circuit


def _give_cirq_gate_name(gate: Gate, name: str, n_qubits: int) -> Gate:
    def _circuit_diagram_info_(args):
        return name, *(name,) * (n_qubits - 1)

    gate._circuit_diagram_info_ = _circuit_diagram_info_


def _create_unitary_gate_cirq(matrix: np.ndarray) -> MatrixGate:
    n_qubits = int(np.log2(len(matrix)))
    unitary_gate = MatrixGate(matrix)
    _give_cirq_gate_name(unitary_gate, "U", n_qubits)
    return unitary_gate


def _unitary_cirq(circuit: Circuit) -> np.ndarray:
    """Calculate unitary of a cirq circuit."""
    return circuit.unitary()
