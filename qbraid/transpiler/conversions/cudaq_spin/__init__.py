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
Conversions from CUDA-Q ``SpinOperator``.

.. currentmodule:: qbraid.transpiler.conversions.cudaq_spin

.. autosummary::
   :toctree: ../stubs/

   cudaq_spin_to_braket_observable
   cudaq_spin_to_cirq_pauli
   cudaq_spin_to_openfermion_qubit
   cudaq_spin_to_pennylane_pauli
   cudaq_spin_to_qiskit_pauli

"""
from .cudaq_spin_extras import (
    cudaq_spin_to_braket_observable,
    cudaq_spin_to_cirq_pauli,
    cudaq_spin_to_openfermion_qubit,
    cudaq_spin_to_pennylane_pauli,
    cudaq_spin_to_qiskit_pauli,
)

__all__ = [
    "cudaq_spin_to_braket_observable",
    "cudaq_spin_to_cirq_pauli",
    "cudaq_spin_to_openfermion_qubit",
    "cudaq_spin_to_pennylane_pauli",
    "cudaq_spin_to_qiskit_pauli",
]
