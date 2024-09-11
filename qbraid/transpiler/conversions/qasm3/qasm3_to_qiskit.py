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

from qbraid.passes.qasm3.compat import add_stdgates_include, insert_gate_def, replace_gate_name
from qbraid.transpiler.annotations import weight

qiskit_qasm3 = LazyLoader("qiskit_qasm3", globals(), "qiskit.qasm3")


if TYPE_CHECKING:
    import qiskit as qiskit_

    from qbraid.programs.typer import Qasm3StringType


def transform_notation(qasm3: str) -> str:
    """
    Process an OpenQASM 3 program that was generated by
    an external tool to make it compatible with Qiskit.

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

    for old, new in replacements.items():
        qasm3 = replace_gate_name(qasm3, old, new)
    qasm3 = add_stdgates_include(qasm3)
    qasm3 = insert_gate_def(qasm3, "iswap")
    qasm3 = insert_gate_def(qasm3, "sxdg")

    return qasm3


@weight(1)
def qasm3_to_qiskit(qasm: Qasm3StringType) -> qiskit_.QuantumCircuit:
    """Convert QASM 3.0 string to a Qiskit QuantumCircuit representation.

    Args:
        qasm (str): A string in QASM 3.0 format.

    Returns:
        qiskit.QuantumCircuit: A QuantumCircuit object representing the input QASM 3.0 string.
    """
    try:
        return qiskit_qasm3.loads(qasm)
    except qiskit_qasm3.QASM3ImporterError:
        pass

    qasm = transform_notation(qasm)

    return qiskit_qasm3.loads(qasm)
