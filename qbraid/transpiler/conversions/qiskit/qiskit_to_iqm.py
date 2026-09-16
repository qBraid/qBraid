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

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import iqm.iqm_client
    import qiskit

iqm_client = LazyLoader("iqm_client", globals(), "iqm.iqm_client")
qiskit_to_iqm_ = LazyLoader("qiskit_to_iqm_", globals(), "iqm.qiskit_iqm.qiskit_to_iqm")

LOGICAL_QUBIT_PREFIX = "q_"


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
        circuit (qiskit.QuantumCircuit): Qiskit circuit, already in the IQM
            native gate set (``r``/``prx`` and ``cz``).

    Returns:
        iqm.iqm_client.Circuit: IQM circuit equivalent to the input circuit.
    """
    index_to_name = {index: logical_qubit_name(index) for index in range(circuit.num_qubits)}
    instructions = tuple(qiskit_to_iqm_.serialize_instructions(circuit, index_to_name))
    return iqm_client.Circuit(name=circuit.name, instructions=instructions, metadata=None)
