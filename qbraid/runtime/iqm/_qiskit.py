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
``iqm.pulse`` circuit objects, while qBraid compiles user programs as
``qiskit.QuantumCircuit`` instances. The actual qiskit-to-IQM conversion logic
comes from ``iqm-client[qiskit]``; this module only keeps the import lazy and
adapts IQM's result formatting into qBraid's result-data shape.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

import numpy as np
from qiskit import QuantumCircuit

from . import _compat


def serialize_circuit(
    circuit: QuantumCircuit,
    *,
    qubit_index_to_name: dict[int, str],
    circuit_cls,
) -> Any:
    """Serialize a qiskit circuit into an IQM circuit object."""
    # IQM's qiskit adapter owns the instruction-level conversion rules.
    instructions = tuple(
        _compat.load_iqm_qiskit_symbols().serialize_instructions(circuit, qubit_index_to_name)
    )

    metadata = circuit.metadata
    if metadata is not None:
        try:
            json.dumps(metadata)
        except TypeError:
            metadata = None

    return circuit_cls(name=circuit.name, instructions=instructions, metadata=metadata)


def format_measurement_results(
    measurement_results: dict[str, list[list[int]]],
) -> tuple[list[str], np.ndarray, dict[str, int]]:
    """Convert IQM measurement results into memory strings, shot arrays and counts."""
    # IQM's qiskit adapter already defines the classical-register ordering and
    # bitstring layout, so qBraid only derives its array/count views from that.
    memory = _compat.load_iqm_qiskit_symbols().format_measurement_results(
        measurement_results,
        0,
        False,
    )
    bitstrings = [item.replace(" ", "") for item in memory]
    measurements = (
        np.array([[int(bit) for bit in bitstring] for bitstring in bitstrings], dtype=int)
        if bitstrings
        else np.empty((0, 0), dtype=int)
    )
    counts = dict(sorted(Counter(bitstrings).items()))
    return memory, measurements, counts
