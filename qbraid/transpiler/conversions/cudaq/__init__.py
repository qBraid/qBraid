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
CUDA-Q conversions

.. currentmodule:: qbraid.transpiler.conversions.cudaq

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   cudaq_to_qasm2
   cudaq_to_pyqir

"""
from .cudaq_extras import cudaq_to_pyqir
from .cudaq_to_qasm2 import cudaq_to_qasm2

__all__ = ["cudaq_to_qasm2", "cudaq_to_pyqir"]
