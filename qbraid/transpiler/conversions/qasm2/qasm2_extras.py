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

if TYPE_CHECKING:
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
