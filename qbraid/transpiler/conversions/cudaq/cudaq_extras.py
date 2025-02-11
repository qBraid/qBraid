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
Module defining CUDA-Q conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cudaq
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    from cudaq import PyKernel
    from pyqir import Module

pyqir = LazyLoader("pyqir", globals(), "pyqir")


@requires_extras("pyqir")
def cudaq_to_pyqir(kernel: PyKernel) -> Module:
    """Converts a CUDA-Q kernel to PyQIR."""
    llvm_ir = cudaq.translate(kernel, format="qir")
    context = pyqir.Context()
    module = pyqir.Module.from_ir(context, llvm_ir, "main")
    return module
