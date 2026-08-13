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

"""
Qiskit helpers for the IQM runtime integration.

qBraid still needs a thin wrapper here because IQM submission expects
``iqm.pulse.Circuit`` Python objects, while qBraid compiles user programs as
``qiskit.QuantumCircuit`` instances. The instruction conversion itself comes
from ``iqm-client[qiskit]``.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader
from qiskit import QuantumCircuit

if TYPE_CHECKING:
    from iqm.iqm_client import Circuit

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")
iqm_qiskit = LazyLoader(
    "iqm_qiskit",
    globals(),
    "iqm.qiskit_iqm.qiskit_to_iqm",
)


def serialize_circuit(
    circuit: QuantumCircuit,
    *,
    qubit_index_to_name: dict[int, str],
) -> Circuit:
    """Convert a Qiskit circuit into an ``iqm.pulse.Circuit`` Python object.

    IQM sends circuit metadata through a JSON API. Non-JSON-serializable Qiskit
    metadata is therefore omitted so otherwise valid circuits can still be
    submitted.
    """
    # IQM's qiskit adapter owns the instruction-level conversion rules.
    instructions = tuple(iqm_qiskit.serialize_instructions(circuit, qubit_index_to_name))

    metadata = circuit.metadata
    if metadata is not None:
        try:
            json.dumps(metadata)
        except (TypeError, ValueError):
            metadata = None

    return iqm_client.Circuit(
        name=circuit.name,
        instructions=instructions,
        metadata=metadata,
    )
