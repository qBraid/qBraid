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
Module for conversions from QASM 2 to Cirq Circuits

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyqasm
from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")
cirq_qasm_parser = LazyLoader(
    "cirq_qasm_parser", globals(), "qbraid.transpiler.conversions.qasm2.cirq_qasm_parser"
)

if TYPE_CHECKING:
    import cirq

    from qbraid.programs.typer import Qasm2StringType
    from qbraid.transpiler.conversions.qasm2.cirq_qasm_parser import QasmParser


@weight(1)
def qasm2_to_cirq(qasm: Qasm2StringType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input QASM string.

    Args:
        qasm: QASM string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input QASM string.
    """
    try:
        qasm_module = pyqasm.loads(qasm)
        qasm_module.unroll(external_gates=["rzz"])
        if qasm_module.has_barriers():
            logger.warning(
                "Barriers are not supported in Cirq, "
                "and will be removed during program conversion."
            )
            qasm_module.remove_barriers()
        parser: QasmParser = cirq_qasm_parser.QasmParser()
        qasm_compat = pyqasm.dumps(qasm_module)
        qasm_parsed = parser.parse(qasm_compat)
        return qasm_parsed.circuit
    except cirq_qasm_import.QasmException as err:
        raise QasmError(err) from err
