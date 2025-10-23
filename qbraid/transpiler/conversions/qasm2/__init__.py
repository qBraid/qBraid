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
OpenQASM 2 conversions

.. currentmodule:: qbraid.transpiler.conversions.qasm2

Functions
----------

.. autosummary::
    :toctree: ../stubs/

    qasm2_to_cirq
    qasm2_to_pytket
    qasm2_to_qiskit
    qasm2_to_qasm3
    qasm2_to_ionq
    qasm2_to_qibo
    qibo_to_qasm2
    qasm2_to_pyqpanda3
    pyqpanda3_to_qasm2

"""

from .qasm2_extras import pyqpanda3_to_qasm2, qasm2_to_pyqpanda3, qasm2_to_qibo, qibo_to_qasm2
from .qasm2_to_cirq import qasm2_to_cirq
from .qasm2_to_ionq import qasm2_to_ionq
from .qasm2_to_pytket import qasm2_to_pytket
from .qasm2_to_qasm3 import qasm2_to_qasm3
from .qasm2_to_qiskit import qasm2_to_qiskit

__all__ = [
    "qasm2_to_cirq",
    "qasm2_to_pytket",
    "qasm2_to_qasm3",
    "qasm2_to_qiskit",
    "qasm2_to_ionq",
    "qasm2_to_qibo",
    "qibo_to_qasm2",
    "qasm2_to_pyqpanda3",
    "pyqpanda3_to_qasm2",
]
