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
from typing import List, Tuple, Union, cast

import numpy as np
from cirq import (
    Circuit,
    CircuitDag,
    EigenGate,
    Gate,
    GateOperation,
    GridQubit,
    I,
    LineQubit,
    MatrixGate,
    Moment,
    NamedQubit,
    ops,
)
from cirq.ops import Qid
from cirq.ops.measurement_gate import MeasurementGate

from qbraid.transpiler.interface.cirq_qasm_gates import ZPowGate as QASM_ZPowGate

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


def _append_measurements(circuit: Circuit, measurements: List[Tuple[int, ops.Operation]]) -> None:
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
                for moment, op, _ in circ.findall_operations_with_gate_type(MeasurementGate)
            ]
            circ.batch_remove(measurements)

            for i in range(len(measurements)):
                gate = cast(MeasurementGate, measurements[i][1].gate)
                gate.key = ""

            circ.batch_insert(measurements)

    return CircuitDag.from_circuit(circuit_one) == CircuitDag.from_circuit(circuit_two)


def _give_cirq_gate_name(gate: Gate, name: str, n_qubits: int) -> Gate:
    def _circuit_diagram_info_(args):
        return name, *(name,) * (n_qubits - 1)

    gate._circuit_diagram_info_ = _circuit_diagram_info_


def _create_unitary_gate_cirq(matrix: np.ndarray) -> MatrixGate:
    n_qubits = int(np.log2(len(matrix)))
    unitary_gate = MatrixGate(matrix)
    _give_cirq_gate_name(unitary_gate, "U", n_qubits)
    return unitary_gate
