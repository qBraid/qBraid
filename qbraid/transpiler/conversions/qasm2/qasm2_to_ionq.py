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
Module containing functions to convert between OpenQASM 2 and IonQ JSON format.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import openqasm3_to_ionq

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm2StringType


@weight(1)
def qasm2_to_ionq(qasm: Qasm2StringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM 2 string.
    """
    return openqasm3_to_ionq(qasm)
