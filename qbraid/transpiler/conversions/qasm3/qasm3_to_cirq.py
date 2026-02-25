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
Module for conversions from QASM 3 to Cirq Circuits

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")

if TYPE_CHECKING:
    import cirq

    from qbraid.programs.typer import Qasm3StringType


@weight(1)
def qasm3_to_cirq(qasm: Qasm3StringType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input OpenQASM 3 string.

    Uses Cirq's built-in ``circuit_from_qasm`` which supports both
    OpenQASM 2.0 and 3.0 syntax.

    Args:
        qasm: OpenQASM 3 string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input OpenQASM 3 string.
    """
    try:
        return cirq_qasm_import.circuit_from_qasm(qasm)
    except cirq_qasm_import.QasmException as err:
        raise QasmError(err) from err
