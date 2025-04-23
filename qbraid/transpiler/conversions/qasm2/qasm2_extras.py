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
Module containing OpenQASM 2 conversion extras.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qibo = LazyLoader("qibo", globals(), "qibo")
pyqpanda3 = LazyLoader("pyqpanda3", globals(), "pyqpanda3")

if TYPE_CHECKING:
    import pyqpanda3 as pyqpanda3_  # type: ignore
    import qibo as qibo_  # type: ignore

    from qbraid.programs.typer import Qasm2StringType


@requires_extras("qibo")
def qasm2_to_qibo(qasm: Qasm2StringType) -> qibo_.Circuit:
    """Returns a qibo.Circuit equivalent to the input OpenQASM 2 circuit.

    Args:
        qasm: OpenQASM 2 string to convert to a qibo.Circuit

    Returns:
        qibo.Circuit object equivalent to the input OpenQASM 2 string.
    """
    # Remove problematic comment lines in the qasm code
    lines = [
        line.replace(", ", ",") for line in qasm.split("\n") if not line.strip().startswith("//")
    ]
    # Remove in line problematic comments
    clean_lines = []
    for line in lines:
        clean_line = line.split("//")[0].strip()
        if clean_line:
            clean_lines.append(clean_line)
    qasm = "\n".join(clean_lines)

    return qibo.Circuit.from_qasm(qasm)


@requires_extras("qibo")
def qibo_to_qasm2(circuit: qibo_.Circuit) -> Qasm2StringType:
    """Returns an OpenQASM 2 string equivalent to the input qibo.Circuit.

    Args:
        circuit: qibo.Circuit object to convert to OpenQASM 2 string.

    Returns:
        OpenQASM 2 string equivalent to the input qibo.Circuit.
    """
    return circuit.to_qasm()


@requires_extras("pyqpanda3")
def qasm2_to_pyqpanda3(qasm: Qasm2StringType) -> pyqpanda3_.core.QProg:
    """Returns a pyqpande3.core.QProg equivalent to the input OpenQASM 2 circuit.

    Args:
        qasm: OpenQASM 2 string to convert to a pyqpanda3.core.QProg

    Returns:
        pyqpanda3.core.QProg object equivalent to the input OpenQASM 2 string.
    """
    return pyqpanda3.intermediate_compiler.convert_qasm_string_to_qprog(qasm)


@requires_extras("pyqpanda3")
def pyqpanda3_to_qasm2(circuit: pyqpanda3_.core.QProg) -> Qasm2StringType:
    """Returns an OpenQASM 2 string equivalent to the input pyqpanda3.core.QProg.

    Args:
        circuit: pyqpanda3.core.QProg object to convert to OpenQASM 2 string.

    Returns:
        OpenQASM 2 string equivalent to the input pyqpanda3.core.QProg.
    """
    return pyqpanda3.intermediate_compiler.convert_qprog_to_qasm(circuit)
