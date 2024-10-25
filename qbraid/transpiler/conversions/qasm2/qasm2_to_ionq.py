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
from typing import TYPE_CHECKING, Any, Union

import openqasm3.ast

from qbraid.passes.qasm.analyze import has_measurements
from qbraid.passes.qasm.compat import convert_qasm_pi_to_decimal
from qbraid.programs import load_program
from qbraid.programs.gate_model.ionq import IonQProgram
from qbraid.programs.gate_model.qasm2 import OpenQasm2Program
from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm2StringType, QasmStringType

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
    "gpi": "gpi",
    "gpi2": "gpi2",
}

IONQ_TWO_QUBIT_GATE_MAP = {
    "cnot": "cnot",
    "cx": "cnot",
    "CX": "cnot",
    "swap": "swap",
    "zz": "zz",
    "ms": "ms",
}

IONQ_THREE_QUBIT_GATE_MAP = {
    "ccx": "cnot",
    "toffoli": "cnot",
}


def extract_params(statement: openqasm3.ast.QuantumGate) -> list[str]:
    """Extracts the parameter(s) from a QuantumGate statement.

    Args:
        statement (openqasm3.ast.QuantumGate): QuantumGate statement to extract parameter(s) from.

    Returns:
        Union[str, list[str]]: Parameter(s) extracted from the QuantumGate statement.
    """
    try:
        params: str = re.findall(r"\((.+)\)", openqasm3.dumps(statement))[0]
    except IndexError:
        return []

    return [p.strip(" ") for p in params.split(",")]


def _parse_float_in_range(
    value: str, gate_name: str, param_name: str, bounds: tuple[float, float]
) -> float:

    min_val, max_val = bounds

    err_msg = (
        f"Invalid {param_name} value '{value}' for the '{gate_name}' gate. "
        f"{param_name.capitalize()} must be a float between {min_val} and {max_val}."
    )

    try:
        value = float(value)
    except ValueError as err:
        raise ValueError(err_msg) from err

    if not min_val <= value <= max_val:
        raise ValueError(err_msg)

    return value


def _parse_phase(phase: str, gate_name: str) -> float:
    return _parse_float_in_range(phase, gate_name, "phase", (-1, 1))


def _parse_angle(angle: str, gate_name: str) -> float:
    return _parse_float_in_range(angle, gate_name, "angle", (0, 0.25))


def _parse_gates(program: Union[OpenQasm2Program, OpenQasm3Program]) -> list[dict[str, Any]]:
    program_qubits = program.qubits

    program: openqasm3.ast.Program = program.parsed()

    gates: list[dict[str, Any]] = []

    for statement in program.statements:
        if isinstance(statement, openqasm3.ast.QuantumGate):
            name = statement.name.name
            qubits = statement.qubits
            qubit_values = []

            if len(qubits) == 1 and isinstance(qubits[0], openqasm3.ast.Identifier):
                reg_name = qubits[0].name
                for qreg_name, qubit_id in program_qubits:
                    if qreg_name == reg_name:
                        qubit_values.append(qubit_id)
            else:
                for qubit in qubits:
                    indices = qubit.indices
                    for index in indices:
                        qubit_values.extend(literal.value for literal in index)

            if name in IONQ_ONE_QUBIT_GATE_MAP:
                ionq_name = IONQ_ONE_QUBIT_GATE_MAP[name]
                if ionq_name in ["rx", "ry", "rz"]:
                    angle: str = extract_params(statement)[0]
                    angle_decimal = float(convert_qasm_pi_to_decimal(angle))
                    for qubit in qubit_values:
                        gates.append(
                            {
                                "gate": ionq_name,
                                "target": qubit,
                                "rotation": angle_decimal,
                            }
                        )
                elif ionq_name in ["gpi", "gpi2"]:
                    phase: str = extract_params(statement)[0]
                    phase = _parse_phase(phase, ionq_name)

                    for qubit in qubit_values:
                        gates.append(
                            {
                                "gate": ionq_name,
                                "target": qubit,
                                "phase": float(phase),
                            }
                        )
                else:
                    for qubit in qubit_values:
                        gates.append({"gate": ionq_name, "target": qubit})

            elif name in IONQ_TWO_QUBIT_GATE_MAP:
                ionq_name = IONQ_TWO_QUBIT_GATE_MAP[name]

                if ionq_name == "swap":
                    gates.append({"gate": ionq_name, "targets": qubit_values})

                elif ionq_name == "zz":
                    angle = extract_params(statement)[0]
                    angle = _parse_angle(angle, ionq_name)
                    gates.append(
                        {
                            "gate": ionq_name,
                            "angle": angle,
                            "targets": qubit_values,
                        }
                    )

                elif ionq_name == "ms":
                    params = extract_params(statement)
                    if len(params) not in {2, 3}:
                        raise ValueError(
                            f"Invalid number of parameters for the '{ionq_name}' gate. "
                            f"Expected 2 or 3, got {len(params)}"
                        )

                    phases = [
                        _parse_phase(param, ionq_name) if i < 2 else _parse_phase(param, ionq_name)
                        for i, param in enumerate(params[:2])
                    ]
                    angle = _parse_angle(params[2], ionq_name) if len(params) == 3 else None

                    gate_data = {
                        "gate": ionq_name,
                        "phases": phases,
                        "targets": qubit_values,
                        **({"angle": angle} if angle is not None else {}),
                    }
                    gates.append(gate_data)

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
                raise NotImplementedError(f"Gate '{name}' not supported by IonQ")

    return gates


def qasm_to_ionq(qasm: QasmStringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM string.

    Args:
        qasm (str): OpenQASM string to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM string.
    """
    if has_measurements(qasm):
        raise ValueError("Circuits with measurements are not supported by the IonQDictType")

    program: Union[OpenQasm2Program, OpenQasm3Program] = load_program(qasm)

    gates = _parse_gates(program)

    if len(gates) == 0:
        raise CircuitConversionError("Failed to parse gate data from OpenQASM string.")

    gateset = IonQProgram.determine_gateset(gates)

    return {"qubits": program.num_qubits, "circuit": gates, "gateset": gateset.value}


@weight(1)
def qasm2_to_ionq(qasm: Qasm2StringType) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM 2 string.

    Args:
        qasm (str): OpenQASM 2 string to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM 2 string.
    """
    return qasm_to_ionq(qasm)
