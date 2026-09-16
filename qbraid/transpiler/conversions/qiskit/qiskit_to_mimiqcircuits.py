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
Module defining the ``qiskit -> mimiqcircuits`` conversion.

Builds a native ``mimiqcircuits.Circuit`` from a qiskit circuit by delegating to QPerfect's
``mimiq-qiskit`` package (Apache-2.0, ``mimiq_qiskit.qiskit_to_mimiq``). This registers
``mimiqcircuits`` as a transpiler target, so qBraid routes any supported program to a qiskit circuit
and then to the MIMIQ native circuit (any -> qiskit -> mimiqcircuits). QPerfect maintains the gate
mapping, so it is not reimplemented here.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import mimiqcircuits as mimiqcircuits_
    import qiskit as qiskit_


@requires_extras("mimiq_qiskit")
def qiskit_to_mimiqcircuits(circuit: qiskit_.QuantumCircuit) -> mimiqcircuits_.Circuit:
    """Convert a qiskit ``QuantumCircuit`` to a native ``mimiqcircuits.Circuit``.

    Thin delegator to ``mimiq_qiskit.qiskit_to_mimiq`` — QPerfect's maintained converter — so the
    gate mapping lives with the vendor rather than being duplicated in qBraid.

    Args:
        circuit: The qiskit circuit to convert.

    Returns:
        The equivalent native MIMIQ circuit.
    """
    # pylint: disable-next=import-outside-toplevel
    from mimiq_qiskit import qiskit_to_mimiq as _qiskit_to_mimiq

    return _qiskit_to_mimiq(circuit)
