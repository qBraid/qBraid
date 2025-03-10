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
Module containing OpenQASM to IonQ JSON conversion function

"""
from __future__ import annotations

import re
import warnings
from typing import TYPE_CHECKING, Any, Union

import openqasm3.ast

from qbraid.passes.qasm.compat import convert_qasm_pi_to_decimal
from qbraid.programs import load_program
from qbraid.programs.gate_model.ionq import IONQ_NATIVE_GATES, IonQProgram
from qbraid.programs.gate_model.qasm2 import OpenQasm2Program
from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, QasmStringType

ONE_QUBIT_NON_PARAM = {
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
}

ONE_QUBIT_PARAM_ROT = {
    "p": "rz",
    "rx": "rx",
    "ry": "ry",
    "rz": "rz",
}

ONE_QUBIT_PARAM_PHASE = {
    "gpi": "gpi",
    "gpi2": "gpi2",
}


IONQ_ONE_QUBIT_GATE_MAP = {**ONE_QUBIT_NON_PARAM, **ONE_QUBIT_PARAM_ROT, **ONE_QUBIT_PARAM_PHASE}

TWO_QUBIT_NON_PARAM = {
    "cnot": "cnot",
    "cx": "cnot",
    "swap": "swap",
}

TWO_QUBIT_PARAM_ANGLE = {
    "zz": "zz",
    "rzz": "zz",
}

TWO_QUBIT_PARAM_ANGLE_PHASE = {
    "ms": "ms",
}

IONQ_TWO_QUBIT_GATE_MAP = {
    **TWO_QUBIT_NON_PARAM,
    **TWO_QUBIT_PARAM_ANGLE,
    **TWO_QUBIT_PARAM_ANGLE_PHASE,
}

IONQ_THREE_QUBIT_GATE_MAP = {
    "ccnot": "cnot",
    "ccx": "cnot",
    "toffoli": "cnot",
}

IONQ_THREE_QUBIT_GATE_ALIASES = {
    "ccnot": "ccnot",
    "ccx": "ccnot",
    "toffoli": "ccnot",
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


# pylint: disable-next=too-many-statements
def _parse_gates(program: Union[OpenQasm2Program, OpenQasm3Program]) -> list[dict[str, Any]]:
    program_qubits = program.module._qubit_registers.items()
    original_program: openqasm3.ast.Program = program.module.original_program

    gates: list[dict[str, Any]] = []

    contains_native = False
    non_zz_native_gates = set(IONQ_NATIVE_GATES) - {"zz"}

    # pylint: disable-next=too-many-nested-blocks
    for statement in original_program.statements:
        if isinstance(statement, openqasm3.ast.QuantumGate):
            name = statement.name.name.lower()

            if name == "id":
                continue

            contains_native = (
                contains_native
                or name in non_zz_native_gates
                or (name.startswith("c") and name[1:] in non_zz_native_gates)
            )

            qubits = statement.qubits
            qubit_values = []

            if len(qubits) == 1 and isinstance(qubits[0], openqasm3.ast.Identifier):
                reg_name = qubits[0].name
                for qreg_name, reg_size in program_qubits:
                    if qreg_name == reg_name:
                        qubit_values = list(range(reg_size))
                        break
            else:
                for qubit in qubits:
                    indices = qubit.indices
                    for index in indices:
                        qubit_values.extend(literal.value for literal in index)

            if name in IONQ_ONE_QUBIT_GATE_MAP:
                ionq_name = IONQ_ONE_QUBIT_GATE_MAP[name]
                if ionq_name in ONE_QUBIT_PARAM_ROT:
                    try:
                        angle: str = extract_params(statement)[0]
                    except IndexError as err:
                        raise ValueError(
                            f"Rotation parameter is required for the '{name}' "
                            "gate but was not provided."
                        ) from err
                    angle_decimal = float(convert_qasm_pi_to_decimal(angle))
                    for qubit in qubit_values:
                        gates.append(
                            {
                                "gate": ionq_name,
                                "target": qubit,
                                "rotation": angle_decimal,
                            }
                        )
                elif ionq_name in ONE_QUBIT_PARAM_PHASE:
                    try:
                        phase: str = extract_params(statement)[0]
                    except IndexError as err:
                        raise ValueError(
                            f"Phase parameter is required for the '{name}' "
                            "gate but was not provided."
                        ) from err
                    phase = _parse_phase(phase, ionq_name)

                    for qubit in qubit_values:
                        gates.append(
                            {
                                "gate": ionq_name,
                                "target": qubit,
                                "phase": phase,
                            }
                        )
                else:
                    for qubit in qubit_values:
                        gates.append({"gate": ionq_name, "target": qubit})

            elif name in IONQ_TWO_QUBIT_GATE_MAP:
                ionq_name = IONQ_TWO_QUBIT_GATE_MAP[name]

                if len(qubit_values) != 2:
                    raise ValueError(
                        f"Invalid number of qubits for the '{name}' gate. "
                        f"Expected 2, got {len(qubit_values)}"
                    )

                if ionq_name in TWO_QUBIT_PARAM_ANGLE:
                    try:
                        angle = extract_params(statement)[0]
                    except IndexError as err:
                        raise ValueError(
                            f"Angle parameter is required for the '{name}' "
                            "gate but was not provided."
                        ) from err

                    # Treat zz as 'qis' gate if all other gates are 'qis' gates
                    if name == "rzz" or (
                        ionq_name == "zz" and len(gates) > 0 and contains_native is False
                    ):
                        angle = float(convert_qasm_pi_to_decimal(angle))
                        gates.append(
                            {
                                "gate": ionq_name,
                                "rotation": angle,
                                "targets": qubit_values,
                            }
                        )

                    else:
                        key = "angle"

                        try:
                            angle = _parse_angle(angle, ionq_name)
                        except ValueError as err:
                            #  Treat zz with angle not in [0, 0.25] as 'qis'
                            if ionq_name == "zz" and contains_native is False:
                                key = "rotation"

                                try:
                                    angle = float(convert_qasm_pi_to_decimal(angle))
                                except ValueError:  # pylint: disable=raise-missing-from
                                    raise err
                            else:
                                raise err
                        else:
                            if ionq_name == "zz":
                                contains_native = True

                        gates.append(
                            {
                                "gate": ionq_name,
                                key: angle,
                                "targets": qubit_values,
                            }
                        )

                elif ionq_name in TWO_QUBIT_PARAM_ANGLE_PHASE:
                    params = extract_params(statement)
                    if len(params) not in {2, 3}:  # pragma: no cover
                        raise ValueError(
                            f"Invalid number of parameters for the '{name}' gate. "
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

                elif ionq_name.startswith("c"):
                    gates.append(
                        {
                            "gate": ionq_name,
                            "control": qubit_values[0],
                            "target": qubit_values[1],
                        }
                    )
                else:
                    gates.append({"gate": ionq_name, "targets": qubit_values})

            elif name.startswith("c") and name[1:] in IONQ_ONE_QUBIT_GATE_MAP:
                ionq_name = IONQ_ONE_QUBIT_GATE_MAP[name[1:]]

                if len(qubit_values) != 2:
                    raise ValueError(
                        f"Invalid number of qubits for the '{name}' gate. "
                        f"Expected 2, got {len(qubit_values)}"
                    )

                if ionq_name in ONE_QUBIT_PARAM_ROT:
                    try:
                        angle: str = extract_params(statement)[0]
                    except IndexError as err:
                        raise ValueError(
                            f"Rotation parameter is required for the '{name}' "
                            "gate but was not provided."
                        ) from err
                    angle_decimal = float(convert_qasm_pi_to_decimal(angle))

                    gates.append(
                        {
                            "gate": ionq_name,
                            "control": qubit_values[0],
                            "target": qubit_values[1],
                            "rotation": angle_decimal,
                        }
                    )
                elif ionq_name in ONE_QUBIT_PARAM_PHASE:
                    try:
                        phase: str = extract_params(statement)[0]
                    except IndexError as err:
                        raise ValueError(
                            f"Phase parameter is required for the '{name}' "
                            "gate but was not provided."
                        ) from err
                    phase = _parse_phase(phase, ionq_name)

                    gates.append(
                        {
                            "gate": ionq_name,
                            "control": qubit_values[0],
                            "target": qubit_values[1],
                            "phase": phase,
                        }
                    )
                else:
                    gates.append(
                        {"gate": ionq_name, "control": qubit_values[0], "target": qubit_values[1]}
                    )

            elif name in IONQ_THREE_QUBIT_GATE_MAP:
                ionq_name = IONQ_THREE_QUBIT_GATE_MAP[name]

                if len(qubit_values) != 3:
                    raise ValueError(
                        f"Invalid number of qubits for the '{name}' gate. "
                        f"Expected 3, got {len(qubit_values)}"
                    )
                gates.append(
                    {
                        "gate": ionq_name,
                        "controls": qubit_values[:2],
                        "target": qubit_values[2],
                    }
                )

            else:
                raise ValueError(f"Gate '{name}' not supported by IonQ")

    return gates


@weight(1)
def openqasm3_to_ionq(qasm: Union[QasmStringType, openqasm3.ast.Program]) -> IonQDictType:
    """Returns an IonQ JSON format representation the input OpenQASM program.

    Args:
        qasm (str or openqasm3.ast.Program): OpenQASM program to convert to IonQDict type.

    Returns:
        dict: IonQ JSON format equivalent to input OpenQASM string.

    Raises:
        ProgramConversionError: For failure to parse gate data from OpenQASM string.
    """
    program: Union[OpenQasm2Program, OpenQasm3Program] = load_program(qasm)

    if program._module.has_measurements():
        warnings.warn(
            "Circuit contains measurement gates, which will be ignored "
            "during conversion to the IonQDictType",
            UserWarning,
        )

    gates = _parse_gates(program)

    if len(gates) == 0:
        raise ProgramConversionError("Failed to parse gate data from OpenQASM string.")

    gateset = IonQProgram.determine_gateset(gates)

    return {
        "qubits": program.num_qubits,
        "circuit": gates,
        "gateset": gateset.value,
        "format": "ionq.circuit.v0",
    }
