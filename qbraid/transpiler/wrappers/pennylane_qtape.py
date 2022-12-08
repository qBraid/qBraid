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
Module defining PennylaneQTapeWrapper Class

"""

from pennylane.tape import QuantumTape

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class PennylaneQTapeWrapper(QuantumProgramWrapper):
    """Wrapper class for Pennylane ``QuantumTape`` objects."""

    def __init__(self, tape: QuantumTape):
        """Create a PennylaneQTapeWrapper

        Args:
            tape: the quantum tape object to be wrapped

        """
        super().__init__(tape)

        self._qubits = tape.wires
        self._num_qubits = len(self.qubits)
        self._depth = tape.graph.get_depth()
        self._package = "pennylane"
        self._program_type = "QuantumTape"
