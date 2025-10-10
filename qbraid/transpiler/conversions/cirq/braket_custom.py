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
Module for defining custom Amazon Braket control gate

"""
import itertools
from typing import Any

import braket.ir.jaqcd as ir
import numpy as np
from braket.circuits import Gate, Instruction, QubitSet, circuit
from braket.circuits.gates import Unitary, format_complex
from braket.circuits.serialization import OpenQASMSerializationProperties


class C(Gate):
    """Controlled gate
    Args:
        sub_gate (Gate): Quantum Gate.
        targets (QubitSet): Target qubits.
    """

    def __init__(self, sub_gate: Gate, targets: QubitSet):
        self.sub_gate = sub_gate
        qubit_count = len(targets)
        sub_qubit_count = sub_gate.qubit_count
        self._num_controls = qubit_count - sub_qubit_count
        self._controls = targets[: self._num_controls]
        ascii_symbols = ["C"] * self._num_controls + list(self.sub_gate.ascii_symbols)

        super().__init__(qubit_count=qubit_count, ascii_symbols=ascii_symbols)

    def _extend_matrix(self, sub_matrix: np.ndarray) -> np.ndarray:
        qid_shape = (2,) * self.qubit_count
        control_values = ((1,),) * self._num_controls
        sub_n = len(qid_shape) - self._num_controls
        tensor = np.eye(np.prod(qid_shape, dtype=np.int64).item(), dtype=complex)
        tensor.shape = qid_shape * 2
        sub_tensor = sub_matrix.reshape(qid_shape[self._num_controls :] * 2)
        for control_vals in itertools.product(*control_values):
            active = (*(v for v in control_vals), *(slice(None),) * sub_n) * 2
            tensor[active] = sub_tensor
        return tensor.reshape((np.prod(qid_shape, dtype=np.int64).item(),) * 2)

    def to_matrix(self, *args, **kwargs) -> np.ndarray:  # pylint: disable=unused-argument
        """Returns a matrix representation of the quantum operator

        Returns:
            np.ndarray: A matrix representation of the quantum operator
        """
        sub_matrix = self.sub_gate.to_matrix()
        return self._extend_matrix(sub_matrix)

    def adjoint(self) -> list[Gate]:
        """Returns the adjoint of the gate."""
        return [Unitary(self.to_matrix().conj().T, display_name=f"({self.ascii_symbols})^†")]

    def _to_jaqcd(self, target: QubitSet) -> Any:
        return ir.Unitary.construct(
            targets=list(target),
            matrix=Unitary._transform_matrix_to_ir(self.to_matrix()),
        )

    def _to_openqasm(  # pylint: disable=unused-argument
        self, target: QubitSet, serialization_properties: OpenQASMSerializationProperties, **kwargs
    ) -> str:
        qubits = [serialization_properties.format_target(int(qubit)) for qubit in target]
        formatted_matrix = np.array2string(
            self.to_matrix(),
            separator=", ",
            formatter={"all": lambda x: format_complex(x)},  # pylint: disable=unnecessary-lambda
            threshold=float("inf"),
        ).replace("\n", "")

        return f"#pragma braket unitary({formatted_matrix}) {', '.join(qubits)}"

    @staticmethod
    @circuit.subroutine(register=True)
    def c(targets: QubitSet, sub_gate: Gate) -> Instruction:
        """Registers this function into the circuit class.
        Args:
            targets (QubitSet): Target qubits.
            sub_gate (Gate): Quantum Gate.
        Returns:
            Instruction: Controlled Gate Instruction.
        """
        return Instruction(C(sub_gate, targets), target=targets)


Gate.register_gate(C)
