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

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def qrisp_to_qasm2(qrisp_qc: qrisp_.QuantumCircuit) -> Qasm2StringType:
    """Returns a QASM 2.0 string equivalent to the input Qrisp circuit.

    Args:
        qrisp_qc: Qrisp circuit to convert to a QASM 2.0 string.

    Returns:
        QASM 2.0 string equivalent to the input Qrisp circuit.
    """
    return qrisp_qc.to_qasm2()
