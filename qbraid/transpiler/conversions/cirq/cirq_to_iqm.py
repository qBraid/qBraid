# Copyright 2025 qBraid
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


"""
Module for converting Cirq circuits to IQM circuits.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cirq
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras, weight
from qbraid.transpiler.exceptions import ProgramConversionError

if TYPE_CHECKING:
    import iqm.iqm_client

cirq_iqm = LazyLoader("cirq_iqm", globals(), "iqm.cirq_iqm")
cirq_iqm_serialize = LazyLoader("cirq_iqm_serialize", globals(), "iqm.cirq_iqm.serialize")

LOGICAL_QUBIT_PREFIX = "q_"


def _reject_unresolved_parameters(circuit: cirq.Circuit) -> None:
    """Reject symbolic gate parameters, which IQM's wire format cannot carry.

    Raises:
        ProgramConversionError: If the circuit has unresolved gate parameters.
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
        raise ProgramConversionError(
            f"Cannot convert a Cirq circuit to IQM with unresolved parameters: "
            f"{', '.join(parameters)}. Resolve the parameters before conversion."
        )


def _to_named_qubits(circuit: cirq.Circuit) -> cirq.Circuit:
    """Relabel qubits to the logical names the IQM wire format expects."""
    ordered = sorted(circuit.all_qubits())
    mapping = {
        qubit: cirq.NamedQid(f"{LOGICAL_QUBIT_PREFIX}{index}", dimension=2)
        for index, qubit in enumerate(ordered)
    }
    return circuit.transform_qubits(lambda q: mapping[q])


@weight(1)
@requires_extras("iqm.cirq_iqm")
def cirq_to_iqm(circuit: cirq.Circuit) -> iqm.iqm_client.Circuit:
    """Return an IQM circuit equivalent to the input Cirq circuit.

    Decomposes to IQM's native gate set (``PhasedXPowGate`` and ``CZ``), then
    hands the circuit to IQM's own serializer. Qubits are relabelled to logical
    names ``q_0 … q_n``; ``IQMDevice`` binds them to physical qubits at submit.

    Args:
        circuit (cirq.Circuit): Cirq circuit to convert.

    Returns:
        iqm.iqm_client.Circuit: IQM circuit equivalent to the input circuit.
    """
    _reject_unresolved_parameters(circuit)

    # Fully connected metadata: this conversion decomposes to the IQM gate set only.
    # Topology routing is the device's job, in IQMDevice. IQM rejects an empty
    # connectivity, so metadata is always built for at least two qubits even when the
    # circuit uses fewer -- the extra one is never referenced.
    qubit_count = max(len(circuit.all_qubits()), 2)
    metadata = cirq_iqm.IQMDeviceMetadata.from_qubit_indices(
        qubit_count, [{i, j} for i in range(qubit_count) for j in range(i + 1, qubit_count)]
    )
    native = cirq_iqm.IQMDevice(metadata).decompose_circuit(_to_named_qubits(circuit))
    return cirq_iqm_serialize.serialize_circuit(native)
