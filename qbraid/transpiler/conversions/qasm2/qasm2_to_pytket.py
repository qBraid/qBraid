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

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

pytket_qasm = LazyLoader("pytket_qasm", globals(), "pytket.qasm")

if TYPE_CHECKING:
    import pytket.circuit

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def qasm2_to_pytket(qasm: Qasm2StringType) -> pytket.circuit.Circuit:
    """Returns a pytket circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to a pytket circuit.

    Returns:
        pytket.circuit.Circuit: PyTKET circuit object equivalent to input OpenQASM 2 string.
    """
    return pytket_qasm.circuit_from_qasm_str(qasm)
