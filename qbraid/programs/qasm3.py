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
Module defining OpenQasm3Program Class

"""

import re
from typing import List, Tuple

import numpy as np
from openqasm3.ast import Program, QubitDeclaration
from openqasm3.parser import parse

from qbraid.programs.abc_program import QuantumProgram


class OpenQasm3Program(QuantumProgram):
    """Wrapper class for OpenQASM 3 strings."""

    @property
    def program(self) -> str:
        return self._program

    @program.setter
    def program(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("Program must be an instance of str")
        self._program = value

    def _to_openqasm3(self) -> Program:
        """Converts qasm str to openqasm3 program type"""
        return parse(self.program)

    @property
    def qubits(self) -> List[Tuple[str, int]]:
        """Return the qubits acted upon by the operations in this circuit"""
        program = parse(self.program)

        qubits = []
        for statement in program.statements:
            if isinstance(statement, QubitDeclaration):
                name = statement.qubit.name
                size = statement.size.value if statement.size else 1
                qubits.append((name, size))
        return qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        program = parse(self.program)

        num_qubits = 0
        for statement in program.statements:
            if isinstance(statement, QubitDeclaration):
                num_qubits += statement.size.value
        return num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        # pylint: disable=import-outside-toplevel
        from qiskit.qasm3 import loads

        return loads(self.program).num_clbits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        # pylint: disable=import-outside-toplevel
        from qiskit.qasm3 import loads

        return loads(self.program).depth()

    def _unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""
        # pylint: disable=import-outside-toplevel
        from qiskit.qasm3 import loads
        from qiskit.quantum_info import Operator

        return Operator(loads(self.program)).data

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
            and not s.strip().startswith(("OPENQASM", "include", "qreg", "qubit", "//"))
        ]
        unused_indices = {}
        for qreg, size in self.qubits:
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

    def _contiguous_expansion(self) -> None:
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

        self._program = self.program + expansion_qasm

    def _contiguous_compression(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        qasm_str = self.program
        qreg_list = set(self.qubits)
        qubit_indices = self._get_unused_qubit_indices()
        for reg, indices in qubit_indices.items():
            size = 1
            for qreg in qreg_list:
                if qreg[0] == reg:
                    size = qreg[1]
                    break

            # remove the register declarations which are not used
            if len(indices) == size:
                qasm_str = re.sub(rf"qreg\s+{reg}\s*\[\d+\]\s*;", "", qasm_str)
                qasm_str = re.sub(rf"qubit\s*\[\d+\]\s*{reg}\s*;", "", qasm_str)
                if size == 1:
                    qasm_str = re.sub(rf"qubit\s+{reg}\s*;", "", qasm_str)
                qreg_list.remove((reg, size))

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
            # 1. Check if the registers are present in the mapping
            if name not in qubit_mapping:
                raise ValueError(f"Register {name} not present in the qubit mapping.")

            if not isinstance(qubit_mapping[name], dict):
                raise ValueError(f"Mapping for register {name} is not a dictionary.")

            if len(qubit_mapping[name]) != size:
                raise ValueError(
                    f"Mapping for register {name} is not exact. Map is {qubit_mapping[name]}."
                )

            # 2. If yes, then see whether all the indices of the register are present in the mapping
            #    and are in range and unique

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

            # 3. Check that all the new indices are unique
            if set(new_indices) != old_indices:
                raise ValueError(
                    f"Index map of register {name} is not unique. Map is {qubit_mapping[name]}."
                )

    def apply_qubit_mapping(self, qubit_mapping: dict):
        """Apply qubit mapping for the qasm program

        Args:
            qubit_mapping (dict): A dict containing the qubit mapping for
                                  qasm string

        Returns:
            str: updated qasm string
        """
        if not qubit_mapping:
            print("No qubit mapping provided.")
            return self.program

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
                    self._program = re.sub(
                        rf"{name}\s*\[{old_id}\]", f"{name}[{marker}{new_id}]", self._program
                    )

        # remove the '-' markers
        for name, _ in qubit_decls:
            self._program = re.sub(rf"{name}\[{marker}", f"{name}[", self._program)
        return self.program

    def reverse_qubit_order(self) -> None:
        """Reverse the order of the qubits in the circuit."""

        qubit_decls = self.qubits

        qubit_mapping = {}
        for reg, size in qubit_decls:
            qubit_mapping[reg] = {old_id: size - old_id - 1 for old_id in range(size)}

        return self.apply_qubit_mapping(qubit_mapping)
