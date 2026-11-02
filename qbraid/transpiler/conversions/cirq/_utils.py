# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared validation and measurement ordering for Cirq conversions."""

import re

import cirq

from qbraid.transpiler.exceptions import ProgramConversionError


def _validate_resolved_parameters(circuit: cirq.Circuit, target: str) -> None:
    """Reject unresolved parameters before entering a concrete conversion.

    Args:
        circuit: Cirq circuit to validate.
        target: Name of the concrete target format.

    Raises:
        ProgramConversionError: If the circuit contains unresolved parameters.
    """
    parameters = sorted(
        {
            name
            for operation in circuit.all_operations()
            if operation.qubits
            for name in cirq.parameter_names(operation)
        }
    )
    if parameters:
        names = ", ".join(parameters)
        raise ProgramConversionError(
            f"Cannot convert a Cirq circuit to {target} with unresolved parameters: {names}. "
            "Resolve the parameters before conversion."
        )


_BIT_INDEX = re.compile(r"^(?P<register>.+)_(?P<index>\d+)$")


def _classical_bit_order(measurements: list[cirq.Operation]) -> list[cirq.Operation]:
    """Order measurements by indexed keys, falling back to qubit order.

    QASM-derived circuits key single-qubit measurements ``c_0``, ``c_1``, ..., and that
    suffix -- not the moment the operation happens to sit in -- is the bit position the
    result belongs at: ``measure q[2] -> c[0]`` must land q_2 in bit 0 even though a
    measurement on q_0 may appear earlier. Keys without an index fall back to qubit order,
    matching the readout convention the Braket converters document.

    A circuit measuring into multiple registers merges them in register-name order, since
    cirq keys do not record declaration order. ``cirq -> qasm2`` sorts cregs by the same key
    (#1345), so both routes from cirq to pyquil agree on the qubit-to-bit mapping.
    """
    indexed = []
    for op in measurements:
        match = _BIT_INDEX.match(op.gate.key)
        if match is None or len(op.qubits) != 1:
            return sorted(measurements, key=lambda op: min(op.qubits))
        indexed.append(((match["register"], int(match["index"])), op))
    return [op for _, op in sorted(indexed, key=lambda pair: pair[0])]
