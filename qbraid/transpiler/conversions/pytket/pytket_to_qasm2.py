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
Module containing functions to convert between OpenQASM 2 and PyTKET.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pytket.qasm import circuit_to_qasm_str

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import pytket.circuit

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def pytket_to_qasm2(circuit: pytket.circuit.Circuit) -> Qasm2StringType:
    """Returns an OpenQASM 2 string equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 string equivalent to input pytket circuit.
    """
    return circuit_to_qasm_str(circuit)
