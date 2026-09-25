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
Conversions from Amazon Braket ``Observable``.

.. currentmodule:: qbraid.transpiler.conversions.braket_observable

.. autosummary::
   :toctree: ../stubs/

   braket_observable_to_cirq_pauli
   braket_observable_to_cudaq_spin
   braket_observable_to_openfermion_qubit
   braket_observable_to_pennylane_pauli
   braket_observable_to_qiskit_pauli

"""
from .braket_observable_extras import (
    braket_observable_to_cirq_pauli,
    braket_observable_to_cudaq_spin,
    braket_observable_to_openfermion_qubit,
    braket_observable_to_pennylane_pauli,
    braket_observable_to_qiskit_pauli,
)

__all__ = [
    "braket_observable_to_cirq_pauli",
    "braket_observable_to_cudaq_spin",
    "braket_observable_to_openfermion_qubit",
    "braket_observable_to_pennylane_pauli",
    "braket_observable_to_qiskit_pauli",
]
