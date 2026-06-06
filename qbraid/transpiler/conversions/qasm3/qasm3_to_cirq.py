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

import pyqasm
from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.passes.qasm.compat import normalize_if_blocks, replace_gate_names
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")

if TYPE_CHECKING:
    import cirq

    from qbraid.programs.typer import Qasm3StringType


# Gate aliases that Cirq's built-in QASM parser does not recognize, mapped to
# their Cirq-supported equivalents.
_GATE_ALIASES = {
    "cnot": "cx",
    "si": "sdg",
    "ti": "tdg",
    "v": "sx",
    "vi": "sxdg",
    "phaseshift": "p",
    "cphaseshift": "cp",
}


@weight(1)
def qasm3_to_cirq(qasm: Qasm3StringType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input OpenQASM 3 string.

    Cirq's built-in importer handles most OpenQASM 2/3 directly, including
    single-line conditionals. When it cannot, the program is normalized into a
    form Cirq accepts -- gate aliases renamed, custom gates unrolled, barriers
    removed, and QASM 3 braced ``if`` blocks rewritten to single-line syntax --
    and parsing is retried.

    Args:
        qasm: OpenQASM 3 string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input OpenQASM 3 string.
    """
    try:
        return cirq_qasm_import.circuit_from_qasm(qasm)
    except cirq_qasm_import.QasmException:
        pass

    try:
        qasm = replace_gate_names(qasm, _GATE_ALIASES)
        qasm_module = pyqasm.loads(qasm)
        qasm_module.unroll(external_gates=["rzz"])
        if qasm_module.has_barriers():
            logger.warning(
                "Barriers are not supported in Cirq, "
                "and will be removed during program conversion."
            )
            qasm_module.remove_barriers()
        qasm = normalize_if_blocks(pyqasm.dumps(qasm_module))
        return cirq_qasm_import.circuit_from_qasm(qasm)
    except cirq_qasm_import.QasmException as err:
        raise QasmError(err) from err
