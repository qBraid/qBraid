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
Module for converting Qiskit circuits to IQM circuits.

"""
from __future__ import annotations

import json
import warnings
from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras
from qbraid.transpiler.exceptions import ProgramConversionError

if TYPE_CHECKING:
    import iqm.iqm_client
    import qiskit

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")
qiskit_ = LazyLoader("qiskit_", globals(), "qiskit")
qiskit_to_iqm_ = LazyLoader("qiskit_to_iqm_", globals(), "iqm.qiskit_iqm.qiskit_to_iqm")

LOGICAL_QUBIT_PREFIX = "q_"
IQM_BASIS_GATES = ["r", "cz"]


def _json_safe(metadata) -> bool:
    """Return whether circuit metadata survives IQM's JSON transport."""
    if metadata is None:
        return False
    try:
        json.dumps(metadata)
    except (TypeError, ValueError):
        warnings.warn(
            f"Dropping circuit metadata that is not JSON serializable: {type(metadata)}.",
            stacklevel=3,
        )
        return False
    return True


def logical_qubit_name(index: int) -> str:
    """Return the device-independent qubit name used by this conversion."""
    return f"{LOGICAL_QUBIT_PREFIX}{index}"


@requires_extras("iqm.qiskit_iqm")
def qiskit_to_iqm(circuit: qiskit.QuantumCircuit) -> iqm.iqm_client.Circuit:
    """Return an IQM circuit equivalent to the input qiskit circuit.

    The IQM wire format addresses qubits by name. This conversion has no device
    context, so it emits logical names ``q_0 … q_n`` and leaves binding them to
    physical qubits to ``IQMDevice``, which passes a ``qubit_mapping`` at submit.

    Args:
        circuit (qiskit.QuantumCircuit): Qiskit circuit to convert.

    Returns:
        iqm.iqm_client.Circuit: IQM circuit equivalent to the input circuit.
    """
    if circuit.parameters:
        names = ", ".join(sorted(str(parameter) for parameter in circuit.parameters))
        raise ProgramConversionError(
            f"Cannot convert a Qiskit circuit to IQM with unresolved parameters: {names}. "
            "Resolve the parameters before conversion."
        )

    # Gate set only: no coupling map, so this stays device-independent. Routing onto a
    # specific topology is IQMDevice.transform's job.
    native = qiskit_.transpile(circuit, basis_gates=IQM_BASIS_GATES, optimization_level=1)
    index_to_name = {index: logical_qubit_name(index) for index in range(native.num_qubits)}
    instructions = tuple(qiskit_to_iqm_.serialize_instructions(native, index_to_name))
    metadata = circuit.metadata if _json_safe(circuit.metadata) else None
    return iqm_client.Circuit(name=circuit.name, instructions=instructions, metadata=metadata)
