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
Module defining Qiskit OpenQASM conversions

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

qiskit = LazyLoader("qiskit", globals(), "qiskit")

if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def qasm2_to_qiskit(qasm: Qasm2StringType) -> qiskit_.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm: OpenQASM 2 string to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input OpenQASM 2 string.
    """
    return qiskit.QuantumCircuit.from_qasm_str(qasm)
