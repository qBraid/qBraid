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
OpenQASM 3 conversions

.. currentmodule:: qbraid.transpiler.conversions.qasm3

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   qasm3_to_braket
   qasm3_to_openqasm3
   qasm3_to_qiskit
   qasm3_to_pyqir
   qasm3_to_ionq
   autoqasm_to_qasm3

"""
from .qasm3_extras import autoqasm_to_qasm3, qasm3_to_pyqir
from .qasm3_to_braket import qasm3_to_braket
from .qasm3_to_ionq import qasm3_to_ionq
from .qasm3_to_openqasm3 import qasm3_to_openqasm3
from .qasm3_to_qiskit import qasm3_to_qiskit

__all__ = [
    "qasm3_to_braket",
    "qasm3_to_openqasm3",
    "qasm3_to_qiskit",
    "qasm3_to_pyqir",
    "qasm3_to_ionq",
    "autoqasm_to_qasm3",
]
