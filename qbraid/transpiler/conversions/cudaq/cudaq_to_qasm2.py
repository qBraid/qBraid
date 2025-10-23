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
