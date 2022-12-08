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
Module defining PyQuilProgramWrapper Class

"""
from pyquil import Program

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class PyQuilProgramWrapper(QuantumProgramWrapper):
    """Wrapper class for pyQuil ``Program`` objects."""

    def __init__(self, program: Program):
        """Create a PyQuilProgramWrapper

        Args:
            program: the program object to be wrapped

        """
        super().__init__(program)

        self._qubits = program.get_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(program)
        self._package = "pyquil"
        self._program_type = "Program"
