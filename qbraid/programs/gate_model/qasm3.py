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
Module defining OpenQasm3Program class.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pyqasm

from qbraid.passes.qasm import normalize_qasm_gate_params, rebase
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import Qasm3String, Qasm3StringType

from ._model import GateModelProgram

if TYPE_CHECKING:
    import qbraid.runtime


def auto_reparse(func):
    """Decorator that ensures the quantum circuit's state
    is validated and reparsed after method execution."""

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._module.validate()
        self._program = str(self._module)
        return result

    return wrapper


class OpenQasm3Program(GateModelProgram):
    """Wrapper class for OpenQASM 3 strings."""

    def __init__(self, program: Qasm3StringType):
        super().__init__(program)
        if not isinstance(program, Qasm3String):
            raise ProgramTypeError(message=f"Expected 'str' object, got '{type(program)}'.")
        self._program: str = program
        self._module = pyqasm.loads(program)

    @property
    def module(self) -> pyqasm.Module:
        """Return the pyqasm module."""
        return self._module

    @property
    def qubits(self) -> dict[str, int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._module._qubit_registers

    @property
    def clbits(self) -> dict[str, int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._module._classical_registers

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
        """Return the unrolled circuit depth (i.e., length of critical path)."""
        return self._module.depth(decompose_native_gates=False)

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        raise NotImplementedError

    def validate(self) -> None:
        """Validate the quantum circuit."""
        self._module.validate()

    @auto_reparse
    def populate_idle_qubits(self) -> None:
        """Converts OpenQASM 3 string to contiguous qasm3 string with gate expansion."""
        self._module.populate_idle_qubits()

    @auto_reparse
    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        self._module.remove_idle_qubits()

    @auto_reparse
    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""
        self._module.validate()
        self._module.reverse_qubit_order()

    def transform(self, device: qbraid.runtime.QuantumDevice, **kwargs) -> None:
        """Transform program to according to device target profile."""
        basis_gates = device.profile.get("basis_gates")

        if basis_gates is not None and len(basis_gates) > 0:
            transformed_qasm = rebase(self.program, basis_gates, **kwargs)
            self._program = normalize_qasm_gate_params(transformed_qasm)
            self._module.validate()

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        return {"openQasm": pyqasm.dumps(self.module)}
