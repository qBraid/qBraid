# Copyright (C) 2023 qBraid
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
from typing import TYPE_CHECKING, List

from qbraid.programs.abc_program import QuantumProgram
from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm

if TYPE_CHECKING:
    import numpy as np


class OpenQasm2Program(QuantumProgram):
    """Wrapper class for OpenQASM 2 strings."""

    @property
    def program(self) -> str:
        return self._program

    @program.setter
    def program(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Program must be an instance of str")
        self._program = value

    def _get_bits(self, bit_type: str) -> List[str]:
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
    def qubits(self) -> List[str]:
        """Use regex to extract all qreg definitions from the string"""
        return self._get_bits("q")

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self._get_bits("c")

    @staticmethod
    def _get_max_count(counts_dict) -> int:
        return max(counts_dict.values()) if counts_dict else 0

    @property
    def depth(self) -> int:  # pylint: disable=too-many-statements
        """Calculates circuit depth of OpenQASM 2 string"""
        qasm_str = self.program
        lines = qasm_str.splitlines()

        # Keywords marking lines to ommit from depth calculation.
        not_counted = ("OPENQASM", "include", "qreg", "creg", "gate", "opaque", "//")
        gate_lines = [s for s in lines if s.strip() and not s.startswith(not_counted)]

        all_qubits = self.qubits
        depth_counts = {qubit: 0 for qubit in all_qubits}

        track_measured = {}

        for _, s in enumerate(gate_lines):
            if s.startswith("barrier"):
                max_depth = self._get_max_count(depth_counts)
                depth_counts = {key: max_depth for key in depth_counts.keys()}
                continue

            raw_matches = re.findall(r"(\w+)\[(\d+)\]", s)

            matches = []
            if len(raw_matches) == 0:
                try:
                    if s.startswith("measure"):
                        match = re.search(r"measure (\w+) -> .+", s)
                        if match:
                            op = match.group(1)
                        else:
                            continue
                    else:
                        op = s.split(" ")[-1].strip(";")
                    for qubit in all_qubits:
                        qubit_name = qubit.split("[")[0]
                        if op == qubit_name:
                            matches.append(qubit)
                # pylint: disable=broad-exception-caught
                except Exception:
                    continue

                if len(matches) == 0:
                    continue
            else:
                for match in raw_matches:
                    var_name = match[0]
                    n = int(match[1])
                    qubit = f"{var_name}[{n}]"
                    if qubit in all_qubits and qubit in depth_counts:
                        matches.append(qubit)

            if s.startswith("if"):
                match = re.search(r"if\((\w+)==\d+\)", s)
                if match:
                    creg = match.group(1)
                    if creg in track_measured:
                        meas_qubits, meas_depth = track_measured[creg]
                        max_measured = max(max(depth_counts[q] for q in meas_qubits), meas_depth)
                        track_measured[creg] = meas_qubits, max_measured + 1
                        qubit = matches[0]
                        depth_counts[qubit] = max(max_measured, depth_counts[qubit]) + 1
                        continue

            # Calculate max depth among the qubits in the current line.
            max_depth = 0
            for qubit in matches:
                max_depth = max(max_depth, depth_counts[qubit])

            # Update depths for all qubits in the current line.
            for qubit in matches:
                depth_counts[qubit] = max_depth + 1

            if s.startswith("measure"):
                match = re.search(r"measure .+ -> (\w+)", s)
                if match:
                    creg = match.group(1)
                    track_measured[creg] = matches, max_depth + 1

        return self._get_max_count(depth_counts)

    def _unitary(self) -> "np.ndarray":
        """Return the unitary of the QASM"""
        return from_qasm(self.program).unitary()

    def _contiguous_expansion(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, adds identity gates to vacant registers as needed."""
        raise NotImplementedError

    def _contiguous_compression(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverses the qubit ordering of a openqasm program."""
        raise NotImplementedError
