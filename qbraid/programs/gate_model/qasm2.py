# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining OpenQasm2Program class.

"""
from __future__ import annotations

import re

import numpy as np
from openqasm3.ast import Program
from openqasm3.parser import parse
from qbraid_core._import import LazyLoader

from qbraid.passes.qasm import depth, normalize_qasm_gate_params, rebase, remove_measurements
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import Qasm2String, Qasm2StringType

from ._model import GateModelProgram

transpiler = LazyLoader("transpiler", globals(), "qbraid.transpiler")


class OpenQasm2Program(GateModelProgram):
    """Wrapper class for OpenQASM 2 strings."""

    def __init__(self, program: Qasm2StringType):
        super().__init__(program)
        if not isinstance(program, Qasm2String):
            raise ProgramTypeError(message=f"Expected 'str' object, got '{type(program)}'.")

    def parsed(self) -> Program:
        """Parse the program string."""
        return parse(self._program)

    def _get_bits(self, bit_type: str) -> list[tuple[str, int]]:
        """Return the number of qubits or classical bits in the circuit.

        Args:
            bit_type: either "q" or "c" for qubits or classical bits, respectively.

        Returns:
            list[tuple[str, int]]: A list of qubits or classical bits. Each bit is
                a tuple of (register name, index)
        """
        matches = re.findall(rf"{bit_type}reg (\w+)\[(\d+)\];", self.program)

        result = []
        for match in matches:
            var_name = match[0]
            n = int(match[1])
            result.extend([(var_name, i) for i in range(n)])
        return result

    @property
    def qubits(self) -> list[tuple[str, int]]:
        """Use regex to extract all qreg definitions from the string"""
        return self._get_bits("q")

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return len(self._get_bits("c"))

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        counts = {q: 0 for q in self.qubits}
        program = self.parsed()
        counts = depth(program.statements, counts)
        return max(counts.values())

    def _unitary(self) -> np.ndarray:
        """Return the unitary of the QASM"""
        return transpiler.transpile(self.program, "cirq").unitary()

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        if device.id == "quera_qasm_simulator":
            self._program = remove_measurements(self.program)

        basis_gates = device.profile.get("basis_gates")

        if basis_gates is not None and len(basis_gates) > 0:
            transformed_qasm = rebase(self.program, basis_gates)
            self._program = normalize_qasm_gate_params(transformed_qasm)
