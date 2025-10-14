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
Module containing OpenQASM conversion function

"""
import pyqasm

from qbraid.programs.typer import Qasm2String, Qasm2StringType, Qasm3StringType
from qbraid.transpiler.annotations import weight


@weight(0.7)
def qasm2_to_qasm3(qasm_str: Qasm2StringType) -> Qasm3StringType:
    """Convert a OpenQASM 2.0 string to OpenQASM 3.0 string

    Args:
        qasm_str (str): OpenQASM 2.0 string

    Returns:
        str: OpenQASM 3.0 string
    """
    if not isinstance(qasm_str, Qasm2String):
        raise ValueError("Invalid OpenQASM 2.0 string")

    qasm_module = pyqasm.loads(qasm_str)
    return qasm_module.to_qasm3(as_str=True)
