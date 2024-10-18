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

from qbraid.passes.qasm.compat import convert_qasm_pi_to_decimal
from qbraid.programs.gate_model.qasm2 import OpenQasm2Program
from qbraid.transpiler.annotations import weight

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm2StringType

IONQ_ONE_QUBIT_GATE_MAP = {
    "x": "x",
    "not": "not",
    "y": "y",
    "z": "z",
    "h": "h",
    "s": "s",
    "si": "si",
    "t": "t",
    "ti": "ti",
    "v": "v",
    "vi": "vi",
    "sdg": "si",
    "tdg": "ti",
    "sx": "v",
    "sxdg": "vi",
    "rx": "rx",
    "ry": "ry",
    "rz": "rz",
}

IONQ_TWO_QUBIT_GATE_MAP = {
    "cnot": "cnot",
    "cx": "cnot",
    "CX": "cnot",
    "swap": "swap",
}

IONQ_THREE_QUBIT_GATE_MAP = {
    "ccx": "cnot",
    "toffoli": "cnot",
}


@weight(1)
def qasm2_to_ionq(qasm: Qasm2StringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM 2 string.
    """

    qprogram = OpenQasm2Program(qasm)
    num_qubits = qprogram.num_qubits
    program_qubits = qprogram.qubits

    program = qprogram.parsed()

    gates: list[dict[str, Any]] = []

    for statement in program.statements:
        if isinstance(statement, openqasm3.ast.QuantumGate):
            name = statement.name.name
            qubits = statement.qubits
            qubit_values = []

            if len(qubits) == 1 and isinstance(qubits[0], openqasm3.ast.Identifier):
                # full register reference here
                reg_name = qubits[0].name
                for qreg_name, qubit_id in program_qubits:
                    if qreg_name == reg_name:
                        qubit_values.append(qubit_id)
            else:
                for qubit in qubits:
                    indices = qubit.indices
                    for index in indices:
                        qubit_values.extend(literal.value for literal in index)

            # support gates defined for IonQ JSON format
            if name in IONQ_ONE_QUBIT_GATE_MAP:
                ionq_name = IONQ_ONE_QUBIT_GATE_MAP[name]
                if ionq_name in ["rx", "ry", "rz"]:
                    # convert "rz(3 * pi / 4) q[0];" to "3 * pi / 4"
                    angle_str = re.findall(r"\((.+)\)", openqasm3.dumps(statement))[0]
                    for qubit in qubit_values:
                        gates.append(
                            {
                                "gate": ionq_name,
                                "target": qubit,
                                "rotation": float(convert_qasm_pi_to_decimal(angle_str)),
                            }
                        )
                else:
                    for qubit in qubit_values:
                        gates.append({"gate": ionq_name, "target": qubit})

            elif name in IONQ_TWO_QUBIT_GATE_MAP:
                ionq_name = IONQ_TWO_QUBIT_GATE_MAP[name]
                if ionq_name == "swap":
                    gates.append({"gate": ionq_name, "targets": qubit_values})
                else:
                    gates.append(
                        {
                            "gate": ionq_name,
                            "control": qubit_values[0],
                            "target": qubit_values[1],
                        }
                    )
            elif name in IONQ_THREE_QUBIT_GATE_MAP:
                gates.append(
                    {
                        "gate": IONQ_THREE_QUBIT_GATE_MAP[name],
                        "controls": qubit_values[:2],
                        "target": qubit_values[2],
                    }
                )
            else:
                raise NotImplementedError(f"'{name}' gate not yet supported")

    return {"qubits": num_qubits, "circuit": gates}
