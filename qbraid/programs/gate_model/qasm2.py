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
Module defining OpenQasm2Program class.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pyqasm
from qbraid_core._import import LazyLoader

from qbraid.passes.qasm import normalize_qasm_gate_params, rebase
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import Qasm2String, Qasm2StringType

from ._model import GateModelProgram

if TYPE_CHECKING:
    import qbraid.runtime

transpiler = LazyLoader("transpiler", globals(), "qbraid.transpiler")


class OpenQasm2Program(GateModelProgram):
    """Wrapper class for OpenQASM 2 strings."""

    def __init__(self, program: Qasm2StringType):
        super().__init__(program)
        if not isinstance(program, Qasm2String):
            raise ProgramTypeError(message=f"Expected 'str' object, got '{type(program)}'.")

        self._module = pyqasm.loads(program)

    @property
    def qubits(self) -> dict[str, int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._module._qubit_registers

    @property
    def module(self) -> pyqasm.Module:
        """Return the pyqasm module."""
        return self._module

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self._module.num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self._module.num_clbits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self._module.depth(decompose_native_gates=False)

    def _unitary(self) -> np.ndarray:
        """Return the unitary of the QASM"""
        raise NotImplementedError

    def validate(self) -> None:
        """Validate the QASM."""
        self._module.validate()

    def transform(self, device: qbraid.runtime.QuantumDevice, **kwargs) -> None:
        """Transform program to according to device target profile."""
        if device.id == "quera_qasm_simulator":
            self._module.unroll()
            self._module.remove_measurements()
            self._program = pyqasm.dumps(self._module)

        basis_gates = device.profile.get("basis_gates")

        if basis_gates is not None and len(basis_gates) > 0:
            transformed_qasm = rebase(self.program, basis_gates, **kwargs)
            self._program = normalize_qasm_gate_params(transformed_qasm)

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        return {"openQasm": pyqasm.dumps(self.module)}
