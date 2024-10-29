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
Module containing functions to convert between OpenQASM 2 and IonQ JSON format.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import openqasm3_to_ionq

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm2StringType


@weight(1)
def qasm2_to_ionq(qasm: Qasm2StringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM 2 string.
    """
    return openqasm3_to_ionq(qasm)
