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
Conversions from OpenFermion ``QubitOperator``.

.. currentmodule:: qbraid.transpiler.conversions.openfermion_qubit

.. autosummary::
   :toctree: ../stubs/

   openfermion_qubit_to_braket_observable
   openfermion_qubit_to_cirq_pauli
   openfermion_qubit_to_cudaq_spin
   openfermion_qubit_to_pennylane_pauli
   openfermion_qubit_to_qiskit_pauli

"""
from .openfermion_qubit_extras import (
    openfermion_qubit_to_braket_observable,
    openfermion_qubit_to_cirq_pauli,
    openfermion_qubit_to_cudaq_spin,
    openfermion_qubit_to_pennylane_pauli,
    openfermion_qubit_to_qiskit_pauli,
)

__all__ = [
    "openfermion_qubit_to_braket_observable",
    "openfermion_qubit_to_cirq_pauli",
    "openfermion_qubit_to_cudaq_spin",
    "openfermion_qubit_to_pennylane_pauli",
    "openfermion_qubit_to_qiskit_pauli",
]
