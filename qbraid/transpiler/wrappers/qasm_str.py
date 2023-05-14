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
Module defining Qasm2CircuitWrapper Class

"""

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper

from qbraid.interface.qbraid_qasm.tools import qasm_qubits, qasm_num_qubits
from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm
from cirq.circuits import Circuit


class QasmCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, qasm_str: str):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped

        """
        # coverage: ignore
        super().__init__(qasm_str)

        self._qubits = qasm_qubits(qasm_str)
        self._num_qubits = qasm_num_qubits(qasm_str)
        self._depth = len(Circuit(from_qasm(qasm_str).all_operations()))
        self._package = "openqasm"
        self._program_type = "str"
