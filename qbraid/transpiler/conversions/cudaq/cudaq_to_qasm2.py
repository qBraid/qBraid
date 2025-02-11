# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining function to convert a CUDA-Q kernel to a QASM2 string.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cudaq

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from cudaq import PyKernel

    from qbraid.programs.typer import Qasm2StringType


@weight(1)
def cudaq_to_qasm2(kernel: PyKernel) -> Qasm2StringType:
    """Converts a CUDA-Q kernel to QASM2."""
    return cudaq.translate(kernel, format="openqasm2")
