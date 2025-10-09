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
Module defining Pennylane OpenQASM conversions

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pennylane.tape import QuantumTape

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def pennylane_to_qasm2(tape: QuantumTape) -> Qasm2StringType:
    """Converts a PennyLane tape to OpenQASM 2.0

    Args:
        tape (QuantumTape): input PennyLane tape

    Returns:
        str: OpenQASM 2.0 representation of the tape

    """
    return tape.to_openqasm(measure_all=False)
