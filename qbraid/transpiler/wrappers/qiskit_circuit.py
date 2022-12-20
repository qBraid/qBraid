# Copyright 2023 qBraid
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
Module defining QiskitCircuitWrapper Class

"""
from cirq import Circuit

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class QiskitCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Qiskit ``Circuit`` objects"""

    def __init__(self, circuit: Circuit):
        """Create a QiskitCircuitWrapper

        Args
            circuit: the qiskit ``Circuit`` object to be wrapped
        """
        super().__init__(circuit)

        self._qubits = circuit.qubits
        self._params = circuit.parameters
        self._num_qubits = circuit.num_qubits
        self._num_clbits = circuit.num_clbits
        self._depth = circuit.depth()
        self._package = "qiskit"
        self._program_type = "QuantumCircuit"
