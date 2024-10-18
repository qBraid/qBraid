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
Module defining OpenQasm3Program class.

"""
from __future__ import annotations

import re
from typing import Optional

import numpy as np
from openqasm3.ast import BitType, ClassicalDeclaration, Program, QubitDeclaration
from openqasm3.parser import parse

from qbraid.passes.qasm import depth, normalize_qasm_gate_params, rebase
from qbraid.passes.qasm.analyze import expression_value_option
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import Qasm3String, Qasm3StringType

from ._model import GateModelProgram


def auto_reparse(func):
    """Decorator that ensures the quantum circuit's state
    is reparsed from QASM after method execution."""

    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self._parse_state()
        return result

    return wrapper


class OpenQasm3Program(GateModelProgram):
    """Wrapper class for OpenQASM 3 strings."""

    def __init__(self, program: Qasm3StringType):
        super().__init__(program)
        if not isinstance(program, Qasm3String):
            raise ProgramTypeError(message=f"Expected 'str' object, got '{type(program)}'.")
        self._program: str = program
        self._parse_state()

    def parsed(self) -> Program:
        """Parse the program string."""
        return parse(self._program)

    def _parse_state(self) -> None:
        """Process the program string."""
        program = self.parsed()

        num_qubits = 0
        num_clbits = 0
        qubits: list[tuple[str, Optional[int]]] = []
        clbits: list[tuple[str, Optional[int]]] = []

        for statement in program.statements:
            if isinstance(statement, QubitDeclaration):
                name = statement.qubit.name
                size = expression_value_option(statement.size)
                qubits.append((name, size))
                num_qubits += 1 if size is None else size
            elif isinstance(statement, ClassicalDeclaration) and isinstance(
                statement.type, BitType
            ):
                name = statement.identifier.name
                size = expression_value_option(statement.type.size)
                clbits.append((name, size))
                num_clbits += 1 if size is None else size

        self._num_qubits = num_qubits
        self._num_clbits = num_clbits
        self._qubits = qubits
        self._clbits = clbits

    @property
    def qubits(self) -> list[tuple[str, Optional[int]]]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def clbits(self) -> list[tuple[str, Optional[int]]]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._clbits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self._num_clbits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        counts = {(q, i): 0 for q, s in self.qubits for i in range(s or 1)}
        program = self.parsed()
        counts = depth(program.statements, counts)
        return max(counts.values())

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        raise NotImplementedError

    @staticmethod
    def _remove_gate_definitions(qasm_str: str) -> str:
        """This is required to account for the case when the gate
        definition has an argument which is having same name as a
        quantum register

        now, if any gate is applied on this argument, it will be
        interpreted as being applied on THE WHOLE register, when it is
        only applied on the argument.

        Example :

        gate custom q1 {
            x q1; // this is STILL DETECTED as a gate application on q1
        }
        qreg q1[4];
        qreg q2[2];
        custom q1[0];
        cx q1[1], q2[1];

        // Actual depth : 1
        // Calculated depth : 2 (because of the gate definition)

        Args:
            qasm_str (string): The qasm string
        Returns:
            qasm_str (string): The qasm string with gate definitions removed
        """
        gate_decls = [x.group() for x in re.finditer(r"(gate)(.*\n)*?\s*\}", qasm_str)]
        for decl in gate_decls:
            qasm_str = qasm_str.replace(decl, "")
        return qasm_str

    def _get_unused_qubit_indices(self) -> dict:
        """Get unused qubit indices in the circuit

        Returns:
            dict: A dictionary with keys as register names and values as sets of unused indices
        """
        qasm_str = self._remove_gate_definitions(self.program)
        lines = qasm_str.splitlines()
        gate_lines = [
            s
            for s in lines
            if s.strip()
            and not s.strip().startswith(("OPENQASM", "include", "qreg", "qubit", "bit", "//"))
        ]
        unused_indices = {}
        for qreg, size in self.qubits:
            size = 1 if size is None else size
            unused_indices[qreg] = set(range(size))

            for line in gate_lines:
                if qreg not in line:
                    continue
                # either qubits or full register is referenced
                used_indices = {int(x) for x in re.findall(rf"{qreg}\[(\d+)\]", line)}
                if len(used_indices) > 0:
                    unused_indices[qreg] = unused_indices[qreg].difference(used_indices)
                else:
                    # full register is referenced
                    unused_indices[qreg] = set()
                    break

                if len(unused_indices[qreg]) == 0:
                    break

        return unused_indices

    @staticmethod
    def _remap_qubits(qasm_str, reg_name, reg_size, unused_indices):
        """Re-map the qubits for a partially used quantum register
        Args:
            qasm_str (str): QASM string
            reg_name (str): name of register
            reg_size (int): original size of register
            unused_indices (set): set of unused indices

        Returns:
            str: updated qasm string"""
        required_size = reg_size - len(unused_indices)

        new_id = 0
        qubit_map = {}
        for idx in range(reg_size):
            if idx not in unused_indices:
                # idx -> new_id
                qubit_map[idx] = new_id
                new_id += 1

        # old_id WILL NEVER match the declaration
        # as it will be < the original size of register

        # 1. Replace the qubits first
        #    as the regex may match the new declaration itself
        for old_id, new_id in qubit_map.items():
            if old_id != new_id:
                qasm_str = re.sub(rf"{reg_name}\s*\[{old_id}\]", f"{reg_name}[{new_id}]", qasm_str)

        # 2. Replace the declaration
        qasm_str = re.sub(
            rf"qreg\s+{reg_name}\s*\[{reg_size}\]\s*;",
            f"qreg {reg_name}[{required_size}];",
            qasm_str,
        )
        qasm_str = re.sub(
            rf"qubit\s*\[{reg_size}\]\s*{reg_name}\s*;",
            f"qubit[{required_size}] {reg_name};",
            qasm_str,
        )
        # 1 qubit register can never be partially used :)

        return qasm_str

    @auto_reparse
    def populate_idle_qubits(self) -> None:
        """Converts OpenQASM 3 string to contiguous qasm3 string with gate expansion.

        No loops OR custom functions supported at the moment.
        """
        # Analyse the qasm3 string for registers and find unused qubits
        qubit_indices = self._get_unused_qubit_indices()
        expansion_qasm = ""

        # Add an identity gate for the unused qubits
        for reg, indices in qubit_indices.items():
            for index in indices:
                expansion_qasm += f"i {reg}[{index}];\n"

        qasm: str = self.program
        self._program = qasm + expansion_qasm

    @auto_reparse
    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        qasm_str: str = self.program
        qreg_list = set(self.qubits)
        qubit_indices = self._get_unused_qubit_indices()
        for reg, indices in qubit_indices.items():
            size = 1
            for qreg in qreg_list:
                if qreg[0] == reg:
                    size = qreg[1] or 1
                    break

            # remove the register declarations which are not used
            if len(indices) == size:
                qasm_str = re.sub(rf"qreg\s+{reg}\s*\[\d+\]\s*;", "", qasm_str)
                qasm_str = re.sub(rf"qubit\s*\[\d+\]\s*{reg}\s*;", "", qasm_str)
                if size == 1:
                    qasm_str = re.sub(rf"qubit\s+{reg}\s*;", "", qasm_str)
                try:
                    qreg_list.remove((reg, size))
                except KeyError:
                    qreg_list.remove((reg, None))

            # resize and re-map the indices of the partially used register
            elif len(indices):
                qasm_str = self._remap_qubits(qasm_str, reg, size, indices)
        self._program = qasm_str

    def _validate_qubit_mapping(self, qubit_decls, qubit_mapping: dict):
        """Validate the supplied qubit map
            qubit mapping structure should be like -
                {
                <reg name> : { old_id : new_id, old_id : new_id, ... },
                ...
                }
        Moreover, every reg should be present in the mapping, even if not being remapped.
        The mapping should be complete and indices should be unique and in range.


        Args:
            qubit_decls (list): Qubit register declarations
            qubit_mapping (dict): A dict containing the qubit mapping for
                                  qasm string
        """

        for name, size in qubit_decls:
            size = 1 if size is None else size

            if name not in qubit_mapping:
                raise ValueError(f"Register {name} not present in the qubit mapping.")

            if not isinstance(qubit_mapping[name], dict):
                raise ValueError(f"Mapping for register {name} is not a dictionary.")

            if len(qubit_mapping[name]) != size:
                raise ValueError(
                    f"Mapping for register {name} is not exact. Map is {qubit_mapping[name]}."
                )

            old_indices = set(range(size))
            new_indices = []

            for idx in old_indices:
                if idx not in qubit_mapping[name]:
                    raise ValueError(f"Index {idx} of register {name} not present in the mapping.")
                if qubit_mapping[name][idx] >= size or qubit_mapping[name][idx] < 0:
                    raise ValueError(
                        f"New index {qubit_mapping[name][idx]} of register {name} is out of range."
                    )
                new_indices.append(qubit_mapping[name][idx])

            if set(new_indices) != old_indices:
                raise ValueError(
                    f"Index map of register {name} is not unique. Map is {qubit_mapping[name]}."
                )

    @auto_reparse
    def apply_qubit_mapping(self, qubit_mapping: dict) -> None:
        """Apply qubit mapping for the qasm program

        Args:
            qubit_mapping (dict): A dict containing the qubit mapping for
                                  qasm string

        Returns:
            str: updated qasm string
        """
        if not qubit_mapping:
            return

        qasm = self._program
        qubit_decls = self.qubits
        self._validate_qubit_mapping(qubit_decls, qubit_mapping)

        # need some placeholder to avoid replacing the same qubit multiple times
        # in case of a CYCLIC mapping

        # Eg. { q : {0:1, 1:0} }
        # In this case if we have
        # cnot q[0], q[1]; and apply the mapping
        # first q[0] -> q[1] and state is -
        # cnot q[1], q[1];
        # second, q[1] -> q[0] and state is -
        # cnot q[0], q[0];

        # this is inconsistent

        marker = "-"
        for name, _ in qubit_decls:
            for old_id, new_id in qubit_mapping[name].items():
                if old_id != new_id:
                    qasm = re.sub(rf"{name}\s*\[{old_id}\]", f"{name}[{marker}{new_id}]", qasm)

        # remove the '-' markers
        for name, _ in qubit_decls:
            qasm = re.sub(rf"{name}\[{marker}", f"{name}[", qasm)

        self._program = qasm

    @auto_reparse
    def replace_reset_with_ops(self) -> None:
        """This function finds all the reset operations in QASM string,
        and replaces them with measurement and conditional X gate operations.

        TODO: Does not account for bits named with identifiers or than 'c'
        """
        qasm_string: str = self.program
        lines = qasm_string.split("\n")
        transformed_lines = []
        classical_bit_counter = 0

        for line in lines:
            if line.startswith("reset"):
                # Extract the qubit name(s) being reset
                qubit_name = line.split(" ")[1].strip(";")

                # Check if the reset is for multiple qubits
                if "[" in qubit_name and "]" in qubit_name:
                    # For array-type qubits, handle them individually
                    base_name = qubit_name.split("[")[0]
                    indices = qubit_name[qubit_name.find("[") + 1 : qubit_name.find("]")].split(",")
                    for index in indices:
                        # Create new measurement operation
                        transformed_lines.append(
                            f"measure {base_name}[{index}] -> c{classical_bit_counter};"
                        )
                        # Create new conditional operation
                        transformed_lines.append(
                            f"if (c{classical_bit_counter} == 1) x {base_name}[{index}];"
                        )
                        # Increment the classical bit counter
                        classical_bit_counter += 1
                else:
                    # For single qubits, just replace directly
                    transformed_lines.append(f"measure {qubit_name} -> c{classical_bit_counter};")
                    transformed_lines.append(f"if (c{classical_bit_counter} == 1) x {qubit_name};")
                    classical_bit_counter += 1
            else:
                transformed_lines.append(line)

        transformed_qasm_string = "\n".join(transformed_lines)

        self._program = transformed_qasm_string

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""

        qubit_decls = self.qubits

        qubit_mapping = {}
        for reg, size in qubit_decls:
            size = 1 if size is None else size
            qubit_mapping[reg] = {old_id: size - old_id - 1 for old_id in range(size)}

        self.apply_qubit_mapping(qubit_mapping)

    @auto_reparse
    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        basis_gates = device.profile.get("basis_gates")

        if basis_gates is not None and len(basis_gates) > 0:
            transformed_qasm = rebase(self.program, basis_gates)
            self._program = normalize_qasm_gate_params(transformed_qasm)
