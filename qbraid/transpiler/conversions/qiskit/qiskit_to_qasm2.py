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

from qiskit import transpile
from qiskit.qasm2 import QASM2ParseError
from qiskit.qasm2 import dumps as qasm2_dumps
from qiskit.qasm2 import loads as qasm2_loads

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm2StringType


# Qiskit's exporter also accepts gates from its extended qelib1.inc, including
# inside custom definitions. Lower rejected exports to the standard library.
_QASM2_BASIS_GATES = [
    "u3",
    "u2",
    "u1",
    "cx",
    "id",
    "x",
    "y",
    "z",
    "h",
    "s",
    "sdg",
    "t",
    "tdg",
    "rx",
    "ry",
    "rz",
    "cz",
    "cy",
    "ch",
    "ccx",
    "crz",
    "cu1",
    "cu3",
    "swap",
    "cswap",
]


# 1.0, not the 0.999 it carried from 2025-01 (#880): that value matched no benchmark and
# existed only as a hidden tie-break. Verified 2026-08: qiskit gate coverage is 1.0 and
# measured circuits survive with routes through this edge preferred on ties.
@weight(1)
def qiskit_to_qasm2(circuit: qiskit_.QuantumCircuit) -> Qasm2StringType:
    """Returns OpenQASM 2 string equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to OpenQASM 2 string.

    Returns:
        str: OpenQASM 2 representation of the input Qiskit circuit.
    """
    qasm = qasm2_dumps(circuit)
    try:
        qasm2_loads(qasm, strict=True)
    except QASM2ParseError:
        circuit = transpile(circuit, basis_gates=_QASM2_BASIS_GATES, optimization_level=0)
        qasm = qasm2_dumps(circuit)
        qasm2_loads(qasm, strict=True)
    return qasm
