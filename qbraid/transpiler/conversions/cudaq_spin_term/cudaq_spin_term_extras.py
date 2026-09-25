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
Module defining the conversion from a single CUDA-Q ``SpinOperatorTerm`` to a ``SpinOperator``.

"""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    import cudaq

__all__ = ["cudaq_spin_term_to_cudaq_spin"]


@weight(1)
def cudaq_spin_term_to_cudaq_spin(op: cudaq.SpinOperatorTerm) -> cudaq.SpinOperator:
    """Wrap a single CUDA-Q product (e.g. ``spin.x(0) * spin.z(1)``) as a ``SpinOperator``."""
    import cudaq

    return cudaq.SpinOperator(op)
