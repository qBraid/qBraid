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
