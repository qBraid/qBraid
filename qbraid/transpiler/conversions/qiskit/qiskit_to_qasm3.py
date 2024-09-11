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

from qiskit.qasm3 import dumps

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm3StringType


@weight(1)
def qiskit_to_qasm3(circuit: qiskit_.QuantumCircuit) -> Qasm3StringType:
    """Convert qiskit QuantumCircuit to QASM 3.0 string"""
    return dumps(circuit)
