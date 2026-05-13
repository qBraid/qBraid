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

import re
from typing import TYPE_CHECKING

import pyqasm
from ply.lex import LexError
from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.passes.qasm.compat import declarations_to_qasm2, normalize_if_blocks, replace_gate_names
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")
cirq_qasm_parser = LazyLoader(
    "cirq_qasm_parser", globals(), "qbraid.transpiler.conversions.qasm2.cirq_qasm_parser"
)

if TYPE_CHECKING:
    import cirq

    from qbraid.programs.typer import Qasm3StringType
    from qbraid.transpiler.conversions.qasm2.cirq_qasm_parser import QasmParser


@weight(1)
def qasm3_to_cirq(qasm: Qasm3StringType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input OpenQASM 3 string.

    Args:
        qasm: OpenQASM 3 string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input OpenQASM 3 string.
    """
    replacements = {
        "cnot": "cx",
        "si": "sdg",
        "ti": "tdg",
        "v": "sx",
        "vi": "sxdg",
        "phaseshift": "p",
        "cphaseshift": "cp",
    }

    # Fast path: try Cirq's built-in parser directly
    try:
        return cirq_qasm_import.circuit_from_qasm(qasm)
    except (cirq_qasm_import.QasmException, LexError):
        pass

    # Full path: unroll via pyqasm, normalize if blocks, parse with custom parser
    try:
        qasm_module = pyqasm.loads(qasm)
        qasm_module.unroll(external_gates=["rzz"])
        if qasm_module.has_barriers():
            logger.warning(
                "Barriers are not supported in Cirq, "
                "and will be removed during program conversion."
            )
            qasm_module.remove_barriers()
        qasm_compat = pyqasm.dumps(qasm_module)
        qasm_compat = normalize_if_blocks(qasm_compat)
        qasm_compat = declarations_to_qasm2(qasm_compat)
        qasm_compat = qasm_compat.replace("OPENQASM 3.0;", "OPENQASM 2.0;")
        qasm_compat = qasm_compat.replace('include "stdgates.inc";', 'include "qelib1.inc";')
        # Convert QASM3 measurement syntax: c[i] = measure q[j]; -> measure q[j] -> c[i];
        qasm_compat = re.sub(
            r"(\w+(?:\[\d+\])?)\s*=\s*measure\s+(\w+(?:\[\d+\])?)\s*;",
            r"measure \2 -> \1;",
            qasm_compat,
        )
        parser: QasmParser = cirq_qasm_parser.QasmParser()
        qasm_parsed = parser.parse(qasm_compat)
        return qasm_parsed.circuit
    except (cirq_qasm_import.QasmException, LexError):
        pass

    # Fallback: try with gate name replacements via openqasm3 AST
    qasm = replace_gate_names(qasm, replacements)

    try:
        return cirq_qasm_import.circuit_from_qasm(qasm)
    except (cirq_qasm_import.QasmException, LexError) as err:
        raise QasmError(err) from err
