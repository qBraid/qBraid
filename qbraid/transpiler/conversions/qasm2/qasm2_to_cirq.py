# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
