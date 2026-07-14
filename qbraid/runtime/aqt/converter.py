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
Module defining the qiskit -> AQT ``quantum_circuit`` serialization used by ``AQTDevice``.

This is the ``serialize`` hook of the device's :class:`~qbraid.programs.ProgramSpec`: the
qBraid transpiler first routes any supported program to a qiskit ``QuantumCircuit`` (e.g.
``cirq -> qiskit``, ``qasm3 -> qiskit``), then this function converts that circuit into the AQT
native-basis payload. The heavy lifting (decomposition to ``{rz, r, rxx}`` with API-valid angles,
and serialization) is delegated to ``qiskit-aqt-provider``; no hardware connection is required.

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, TypedDict

from qbraid_core._import import LazyLoader

qiskit = LazyLoader("qiskit", globals(), "qiskit")

if TYPE_CHECKING:
    import qiskit as qiskit_typing

# AQT hardware natively implements this basis: virtual-Z (RZ), single-qubit rotation (R),
# and the Molmer-Sorensen entangler (RXX).
AQT_BASIS_GATES = ["rz", "r", "rxx"]

#: A single AQT native operation, e.g. ``{"operation": "RZ", "qubit": 0, "phi": 0.5}``.
AQTOperation = dict[str, Any]


class AQTCircuitPayload(TypedDict):
    """A single AQT ``quantum_circuit`` submission payload, minus ``repetitions``.

    Produced by :func:`qiskit_to_aqt`. ``quantum_circuit`` is the ordered list of AQT native
    operations (``RZ`` / ``R`` / ``RXX`` / ``MEASURE``) and ``number_of_qubits`` is the circuit's
    register size. ``repetitions`` (shots) is added per circuit at submit time.
    """

    quantum_circuit: list[AQTOperation]
    number_of_qubits: int


def qiskit_to_aqt(circuit: qiskit_typing.QuantumCircuit) -> AQTCircuitPayload:
    """Convert a Qiskit ``QuantumCircuit`` into an AQT per-circuit submission payload.

    Args:
        circuit (qiskit.QuantumCircuit): Qiskit quantum circuit.

    Returns:
        AQTCircuitPayload: ``{"quantum_circuit": [...operations...], "number_of_qubits": <int>}``
            — the arnica per-circuit payload without ``repetitions`` (added at submit time). The
            ``number_of_qubits`` is taken directly from the circuit's ``num_qubits`` property.
    """
    # pylint: disable-next=import-outside-toplevel
    from qiskit_aqt_provider.circuit_to_aqt import qiskit_to_aqt_circuit

    with warnings.catch_warnings():
        # The AQT scheduling stage warns about missing instruction durations when run without a
        # backend; it is only used here for its angle-wrapping passes, so the warning is benign.
        warnings.simplefilter("ignore", UserWarning)
        transpiled = qiskit.transpile(
            circuit,
            basis_gates=AQT_BASIS_GATES,
            translation_method="aqt",
            scheduling_method="aqt",
            optimization_level=1,
        )
    return {
        "quantum_circuit": qiskit_to_aqt_circuit(transpiled).model_dump(),
        "number_of_qubits": circuit.num_qubits,
    }
