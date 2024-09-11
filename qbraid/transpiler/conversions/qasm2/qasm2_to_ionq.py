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
Module containing functions to convert between OpenQASM 2 and IonQ JSON format.

"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import openqasm3.ast

from qbraid.passes.qasm3.compat import convert_qasm_pi_to_decimal
from qbraid.programs.circuits.qasm import OpenQasm2Program
from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm2StringType


@weight(1)
def qasm2_to_ionq(qasm: Qasm2StringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to a pytket circuit.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM 2 string.
    """

    qprogram = OpenQasm2Program(qasm)
    num_qubits = qprogram.num_qubits

    program = qprogram.parsed()

    gates: list[dict[str, Any]] = []

    for statement in program.statements:
        if isinstance(statement, openqasm3.ast.QuantumGate):
            name = statement.name.name
            qubits = statement.qubits
            qubit_values = []

            for qubit in qubits:
                _ = qubit.name.name
                indices = qubit.indices
                for index in indices:
                    qubit_values.extend(literal.value for literal in index)

            # support gates defined in `stdgates.inc` from OpenQASM 3
            if len(qubit_values) == 1:
                # IonQ supported gates:
                if name in ["x", "not", "y", "z", "h", "s", "si", "t", "ti", "v", "vi"]:
                    gate_data = {"gate": name, "target": qubit_values[0]}
                elif name in ["rx", "ry", "rz"]:
                    # convert "rz(3 * pi / 4) q[0];" to "3 * pi / 4"
                    angle_str = re.findall(r"\((.+)\)", openqasm3.dumps(statement))[0]
                    gate_data = {
                        "gate": name,
                        "target": qubit_values[0],
                        "rotation": float(convert_qasm_pi_to_decimal(angle_str)),
                    }
                # OpenQASM 3 aliases:
                elif name == "sdg":
                    gate_data = {"gate": "si", "target": qubit_values[0]}
                elif name == "tdg":
                    gate_data = {"gate": "ti", "target": qubit_values[0]}
                elif name == "sx":
                    gate_data = {"gate": "v", "target": qubit_values[0]}
                elif name == "sxdg":
                    gate_data = {"gate": "vi", "target": qubit_values[0]}
                else:
                    raise NotImplementedError(f"'{name}' gate not yet supported")
            elif len(qubit_values) == 2:
                if name in ["cnot", "cx", "CX"]:
                    gate_data = {
                        "gate": "cnot",
                        "control": qubit_values[0],
                        "target": qubit_values[1],
                    }
                elif name == "swap":
                    gate_data = {
                        "gate": "swap",
                        "targets": qubit_values,
                    }
                else:
                    raise NotImplementedError(f"'{name}' gate not yet supported")
            elif len(qubit_values) == 3:
                if name in ["ccx", "toffoli"]:
                    gate_data = {
                        "gate": "cnot",
                        "controls": qubit_values[:2],
                        "target": qubit_values[2],
                    }
            else:
                raise NotImplementedError(f"'{name}' gate not yet supported")

            gates.append(gate_data)

    return {"qubits": num_qubits, "circuit": gates}
