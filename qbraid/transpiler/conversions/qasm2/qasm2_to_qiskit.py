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
Module defining Qiskit OpenQASM conversions

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

qiskit = LazyLoader("qiskit", globals(), "qiskit")

if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def qasm2_to_qiskit(qasm: Qasm2StringType) -> qiskit_.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input OpenQASM 2 string.

    Args:
        qasm: OpenQASM 2 string to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input OpenQASM 2 string.
    """
    return qiskit.QuantumCircuit.from_qasm_str(qasm)
