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
Module defining OpenQasm2Program Class

"""
import re
from typing import TYPE_CHECKING

from openqasm3.ast import (
    BranchingStatement,
    ClassicalDeclaration,
    IndexedIdentifier,
    Program,
    QuantumBarrier,
    QuantumGate,
    QuantumMeasurementStatement,
    QuantumReset,
    QubitDeclaration,
)
from openqasm3.parser import parse

from qbraid.programs.exceptions import ProgramTypeError

from ._model import GateModelProgram

if TYPE_CHECKING:
    import numpy as np


class OpenQasm2Program(GateModelProgram):
    """Wrapper class for OpenQASM 2 strings."""

    def __init__(self, program: str):
        super().__init__(program)
        if not isinstance(program, str):
            raise ProgramTypeError(message=f"Expected 'str' object, got '{type(program)}'.")

    def parsed(self) -> Program:
        """Parse the program string."""
        return parse(self._program)

    def _get_bits(self, bit_type: str) -> list[str]:
        """Return the number of qubits or classical bits in the circuit.

        Args:
            bit_type: either "q" or "c" for qubits or classical bits, respectively.

        """
        matches = re.findall(rf"{bit_type}reg (\w+)\[(\d+)\];", self.program)

        result = []
        for match in matches:
            var_name = match[0]
            n = int(match[1])
            result.extend([f"{var_name}[{i}]" for i in range(n)])

        return result

    @property
    def qubits(self) -> list[str]:
        """Use regex to extract all qreg definitions from the string"""
        return self._get_bits("q")

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return len(self._get_bits("c"))

    @property
    def depth(self) -> int:  # pylint: disable=too-many-statements
        """Return the circuit depth (i.e., length of critical path)."""

        def _depth(qasm_statements) -> dict:  # pylint: disable=too-many-statements
            """Return the depth of a list ofgiven qasm statements."""
            counts = {q: 0 for q in self.qubits}
            qreg_sizes = {}
            creg_sizes = {}
            track_measured = {}
            max_depth = 0
            for statement in qasm_statements:
                if isinstance(statement, QubitDeclaration):
                    qreg_name = statement.qubit.name
                    qreg_size = statement.size.value
                    qreg_sizes[qreg_name] = qreg_size
                    continue
                if isinstance(statement, ClassicalDeclaration):
                    creg_name = statement.identifier.name
                    creg_size = statement.type.size.value
                    creg_sizes[creg_name] = creg_size
                    for i in range(creg_size):
                        track_measured[f"{creg_name}[{i}]"] = 0
                    continue
                if isinstance(statement, QuantumGate):
                    qubits_involved = set()
                    if isinstance(statement.qubits[0], IndexedIdentifier):
                        for qubit in statement.qubits:
                            qreg_name = qubit.name.name
                            qubit_index = qubit.indices[0][0].value
                            counts[f"{qreg_name}[{qubit_index}]"] += 1
                            qubits_involved.add(f"{qreg_name}[{qubit_index}]")
                        max_involved_depth = max(counts[qubit] for qubit in qubits_involved)
                        for qubit in qubits_involved:
                            counts[qubit] = max_involved_depth
                    else:
                        for qubit in statement.qubits:
                            qreg_name = qubit.name
                            for i in range(qreg_sizes[qreg_name]):
                                counts[f"{qreg_name}[{i}]"] += 1
                    max_depth = max(counts.values())
                elif isinstance(statement, QuantumReset):
                    if isinstance(statement.qubits, IndexedIdentifier):
                        qreg_name = statement.qubits.name.name
                        qubit_index = statement.qubits.indices[0][0].value
                        counts[f"{qreg_name}[{qubit_index}]"] += 1
                    else:
                        qreg_name = statement.qubits.name
                        for i in range(qreg_sizes[qreg_name]):
                            counts[f"{qreg_name}[{i}]"] += 1
                elif isinstance(statement, QuantumBarrier):
                    for qubit in statement.qubits:
                        qreg_name = qubit.name
                        for i in range(qreg_sizes[qreg_name]):
                            counts[f"{qreg_name}[{i}]"] = max_depth
                elif isinstance(statement, QuantumMeasurementStatement):
                    qubit = statement.measure.qubit
                    if isinstance(qubit, IndexedIdentifier):
                        qreg_name = qubit.name.name
                        qubit_index = qubit.indices[0][0].value
                        counts[f"{qreg_name}[{qubit_index}]"] += 1
                        creg_name = statement.target.name.name
                        creg_index = statement.target.indices[0][0].value
                        max_depth = max(counts.values())
                        track_measured[f"{creg_name}[{creg_index}]"] = max_depth
                    else:
                        qreg_name = qubit.name
                        for i in range(qreg_sizes[qreg_name]):
                            counts[f"{qreg_name}[{i}]"] += 1
                        creg = statement.target.name
                        max_depth = max(counts.values())
                        for i in range(creg_sizes[creg]):
                            track_measured[f"{creg}[{i}]"] = max_depth
                elif isinstance(statement, BranchingStatement):
                    creg_name = statement.condition.lhs.name
                    required_depth = max(
                        track_measured[f"{creg_name}[{creg_index}]"]
                        for creg_index in range(creg_sizes[creg_name])
                    )
                    required_depth = max(required_depth, max_depth)
                    for i in range(creg_sizes[creg_name]):
                        track_measured[f"{creg_name}[{i}]"] = required_depth
                    qubits = set()
                    for sub_statement in statement.if_block + statement.else_block:
                        if isinstance(sub_statement, QuantumGate):
                            for qubit in sub_statement.qubits:
                                qreg_name = qubit.name.name
                                qubit_index = qubit.indices[0][0].value
                                qubits.add(f"{qreg_name}[{qubit_index}]")
                        elif isinstance(sub_statement, QuantumMeasurementStatement):
                            qreg_name = sub_statement.measure.qubit.name.name
                            qubit_index = sub_statement.measure.qubit.indices[0][0].value
                            qubits.add(f"{qreg_name}[{qubit_index}]")

                    for qubit in qubits:
                        counts[qubit] = max(required_depth, counts[qubit]) + 1

                    max_depth = max(counts.values())
            return counts

        program = self.parsed()
        counts = _depth(program.statements)

        return max(counts.values())

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of the QASM"""
        # pylint: disable=import-outside-toplevel
        from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq

        return qasm2_to_cirq(self.program).unitary()

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverses the qubit ordering of a openqasm program."""
        raise NotImplementedError
