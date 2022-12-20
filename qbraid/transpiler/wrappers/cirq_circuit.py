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

# pylint: disable=invalid-name


"""
Module defining CirqCircuitWrapper Class

"""

from cirq.circuits import Circuit

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class CirqCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, circuit: Circuit):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped

        """
        super().__init__(circuit)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(Circuit(circuit.all_operations()))
        self._package = "cirq"
        self._program_type = "Circuit"
