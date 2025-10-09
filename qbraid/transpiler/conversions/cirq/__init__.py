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
Cirq conversions

.. currentmodule:: qbraid.transpiler.conversions.cirq

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   cirq_to_braket
   cirq_to_qasm2
   cirq_to_pyquil
   cirq_to_pyqir
   cirq_to_stim
   stim_to_cirq

"""
from .cirq_extras import cirq_to_pyqir, cirq_to_stim, stim_to_cirq
from .cirq_to_braket import cirq_to_braket
from .cirq_to_pyquil import cirq_to_pyquil
from .cirq_to_qasm2 import cirq_to_qasm2

__all__ = [
    "cirq_to_braket",
    "cirq_to_qasm2",
    "cirq_to_pyquil",
    "cirq_to_pyqir",
    "cirq_to_stim",
    "stim_to_cirq",
]
