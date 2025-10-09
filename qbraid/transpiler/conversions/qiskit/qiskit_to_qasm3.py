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

from qiskit.qasm3 import dumps

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm3StringType


@weight(1)
def qiskit_to_qasm3(circuit: qiskit_.QuantumCircuit) -> Qasm3StringType:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)
