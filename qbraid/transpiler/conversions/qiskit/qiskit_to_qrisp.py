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
Module defining Qrisp conversions

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

qrisp = LazyLoader("qrisp", globals(), "qrisp")

if TYPE_CHECKING:
    import qrisp as qrisp_

    import qiskit as qiskit_


@weight(1.0)
def qiskit_to_qrisp(qiskit_qc: qiskit_.QuantumCircuit) -> qrisp_.QuantumCircuit:
    """Returns a Qrisp circuit equivalent to the input Qiskit circuit.

    Args:
        qiskit_qc: Qiskit circuit to convert to a Qrisp circuit.

    Returns:
        Qrisp Circuit equivalent to the input Qiskit circuit.
    """
    from qrisp.interface.converter import convert_from_qiskit  # type: ignore
    from qiskit import transpile
    from qiskit.transpiler import Target

    basis_set = [
        "x",
        "y",
        "z",
        "cx",
        "cy",
        "cz",
        "u3",
        "h",
        "rx",
        "ry",
        "rz",
        "s",
        "t",
        "measure",
        "global_phase",
        "swap",
    ]

    target = Target.from_configuration(basis_gates=basis_set)

    return convert_from_qiskit(transpile(qiskit_qc, target=target, optimization_level=0))
