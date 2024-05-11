# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for transforming Cirq circuits.

"""

from typing import Optional

import cirq
from cirq import value
from cirq.contrib.qasm_import import circuit_from_qasm


def decompose(circuit: "cirq.Circuit", strategy: str = "qasm") -> "cirq.Circuit":
    """
    Flatten a Cirq circuit.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to flatten.
        strategy (str): The decomposition strategy to use. Defaults to 'qasm'.

    Returns:
        cirq.Circuit: The flattened Cirq circuit.

    Raises:
        ValueError: If the decomposition strategy is not supported.

    """
    # TODO: potentially replace with native cirq.decompose
    # https://quantumai.google/reference/python/cirq/decompose

    if strategy == "qasm":
        return circuit_from_qasm(circuit.to_qasm())

    raise ValueError(f"Decomposition strategy '{strategy}' not supported.")


def align_final_measurements(circuit: cirq.Circuit) -> cirq.Circuit:
    """
    Align the final measurement gates of all qubits in the same moment
    if they all end with a measurement.

    Args:
        circuit (cirq.Circuit): The input quantum circuit.

    Returns:
        cirq.Circuit: New circuit where all final measurements are aligned in the same moment.
    """
    new_circuit = cirq.Circuit()

    last_ops = {qubit: None for qubit in circuit.all_qubits()}

    for moment in circuit:
        for op in moment.operations:
            if isinstance(op.gate, cirq.MeasurementGate):
                last_ops[op.qubits[0]] = op

    if all(op is not None for op in last_ops.values()):
        measurement_moment = cirq.Moment()
        for op in last_ops.values():
            measurement_moment = measurement_moment.with_operation(op)
        for moment in circuit:
            non_measurement_moment = cirq.Moment()
            for op in moment.operations:
                if not isinstance(op.gate, cirq.MeasurementGate):
                    non_measurement_moment = non_measurement_moment.with_operation(op)
            if non_measurement_moment.operations:
                new_circuit.append(non_measurement_moment)
        new_circuit.append(measurement_moment)
    else:
        return circuit

    return new_circuit


@value.value_equality
class ZPowGate(cirq.ZPowGate):
    """A single qubit gate for rotations around the
    Z axis of the Bloch sphere.
    """

    def num_qubits(self) -> int:
        """The number of qubits this gate acts on."""
        return 1

    def _qasm_(self, args: "cirq.QasmArgs", qubits: tuple["cirq.Qid", ...]) -> Optional[str]:
        args.validate_version("2.0")
        if self._global_shift == 0:
            if self._exponent == 0.25:
                return args.format("t {0};\n", qubits[0])
            if self._exponent == -0.25:
                return args.format("tdg {0};\n", qubits[0])
            if self._exponent == 0.5:
                return args.format("s {0};\n", qubits[0])
            if self._exponent == -0.5:
                return args.format("sdg {0};\n", qubits[0])
            if self._exponent == 1:
                return args.format("z {0};\n", qubits[0])
            return args.format("p({0:half_turns}) {1};\n", self._exponent, qubits[0])
        return args.format("rz({0:half_turns}) {1};\n", self._exponent, qubits[0])


def map_zpow_and_unroll(circuit: cirq.Circuit) -> cirq.Circuit:
    """Map ZPowGate to RZ and unroll circuit"""

    def _map_zpow(op: cirq.Operation, _: int) -> cirq.OP_TREE:
        if isinstance(op.gate, cirq.ZPowGate):
            yield ZPowGate(exponent=op.gate.exponent, global_shift=op.gate.global_shift)(
                op.qubits[0]
            )
        else:
            yield op

    return cirq.map_operations_and_unroll(circuit, _map_zpow)
