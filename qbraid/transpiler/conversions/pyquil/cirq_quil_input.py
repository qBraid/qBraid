# Copyright (C) 2024 qBraid
# Copyright (C) 2020 The Cirq Developers
#
# This file is part of the qBraid-SDK.
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. This specific file, adapted from Cirq, is dual-licensed under both the
# Apache License, Version 2.0, and the GPL v3. You may not use this file except in
# compliance with the applicable license. You may obtain a copy of the Apache License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file includes code adapted from Cirq (https://github.com/quantumlib/Cirq)
# with modifications by qBraid. The original copyright notice is included above.
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# qbraid: skip-header

"""
Module for conversions from Quil to Cirq.

"""

from typing import Callable, Union, cast

import numpy as np
from cirq import Circuit, LineQubit
from cirq.ops import (
    CCNOT,
    CNOT,
    CSWAP,
    CZ,
    ISWAP,
    SWAP,
    CZPowGate,
    Gate,
    H,
    I,
    ISwapPowGate,
    MatrixGate,
    MeasurementGate,
    S,
    T,
    TwoQubitDiagonalGate,
    X,
    Y,
    Z,
    ZPowGate,
    rx,
    ry,
    rz,
)
from pyquil import Program
from pyquil.quilbase import Declare
from pyquil.quilbase import Gate as PyQuilGate
from pyquil.quilbase import Measurement as PyQuilMeasurement
from pyquil.quilbase import Pragma, Reset, ResetQubit


class UndefinedQuilGate(Exception):
    """Raised when a Quil gate is not defined."""


class UnsupportedQuilInstruction(Exception):
    """Raised when a Quil instruction is not supported."""


def cphase(param: float) -> CZPowGate:
    """Returns a controlled-phase gate as a Cirq CZPowGate with exponent
    determined by the input param. The angle parameter of pyQuil's CPHASE
    gate and the exponent of Cirq's CZPowGate differ by a factor of pi.

    Args:
        param: Gate parameter (in radians).

    Returns:
        A CZPowGate equivalent to a CPHASE gate of given angle.
    """
    return CZPowGate(exponent=param / np.pi)


def cphase00(phi: float) -> TwoQubitDiagonalGate:
    """Returns a Cirq TwoQubitDiagonalGate for pyQuil's CPHASE00 gate.

    In pyQuil, CPHASE00(phi) = diag([exp(1j * phi), 1, 1, 1]), and in Cirq,
    a TwoQubitDiagonalGate is specified by its diagonal in radians, which
    would be [phi, 0, 0, 0].

    Args:
        phi: Gate parameter (in radians).

    Returns:
        A TwoQubitDiagonalGate equivalent to a CPHASE00 gate of given angle.
    """
    return TwoQubitDiagonalGate([phi, 0, 0, 0])


def cphase01(phi: float) -> TwoQubitDiagonalGate:
    """Returns a Cirq TwoQubitDiagonalGate for pyQuil's CPHASE01 gate.

    In pyQuil, CPHASE01(phi) = diag(1, [exp(1j * phi), 1, 1]), and in Cirq,
    a TwoQubitDiagonalGate is specified by its diagonal in radians, which
    would be [0, phi, 0, 0].

    Args:
        phi: Gate parameter (in radians).

    Returns:
        A TwoQubitDiagonalGate equivalent to a CPHASE01 gate of given angle.
    """
    return TwoQubitDiagonalGate([0, phi, 0, 0])


def cphase10(phi: float) -> TwoQubitDiagonalGate:
    """Returns a Cirq TwoQubitDiagonalGate for pyQuil's CPHASE10 gate.

    In pyQuil, CPHASE10(phi) = diag(1, 1, [exp(1j * phi), 1]), and in Cirq,
    a TwoQubitDiagonalGate is specified by its diagonal in radians, which
    would be [0, 0, phi, 0].

    Args:
        phi: Gate parameter (in radians).

    Returns:
        A TwoQubitDiagonalGate equivalent to a CPHASE10 gate of given angle.
    """
    return TwoQubitDiagonalGate([0, 0, phi, 0])


def phase(param: float) -> ZPowGate:
    """Returns a single-qubit phase gate as a Cirq ZPowGate with exponent
    determined by the input param. The angle parameter of pyQuil's PHASE
    gate and the exponent of Cirq's ZPowGate differ by a factor of pi.

    Args:
        param: Gate parameter (in radians).

    Returns:
        A ZPowGate equivalent to a PHASE gate of given angle.
    """
    return ZPowGate(exponent=param / np.pi)


def pswap(phi: float) -> MatrixGate:
    """Returns a Cirq MatrixGate for pyQuil's PSWAP gate.

    Args:
        phi: Gate parameter (in radians).

    Returns:
        A MatrixGate equivalent to a PSWAP gate of given angle.
    """
    # fmt: off
    pswap_matrix = np.array(
        [
            [1, 0, 0, 0],
            [0, 0, np.exp(1j * phi), 0],
            [0, np.exp(1j * phi), 0, 0],
            [0, 0, 0, 1]
        ],
        dtype=complex,
    )
    # fmt: on
    return MatrixGate(pswap_matrix)


def xy(param: float) -> ISwapPowGate:
    """Returns an ISWAP-family gate as a Cirq ISwapPowGate with exponent
    determined by the input param. The angle parameter of pyQuil's XY gate
    and the exponent of Cirq's ISwapPowGate differ by a factor of pi.

    Args:
        param: Gate parameter (in radians).

    Returns:
        An ISwapPowGate equivalent to an XY gate of given angle.
    """
    return ISwapPowGate(exponent=param / np.pi)


PRAGMA_ERROR = """
Please remove PRAGMAs from your Quil program.
If you would like to add noise, do so after conversion.
"""

RESET_ERROR = """
Please remove RESETs from your Quil program.
RESET directives have special meaning on QCS, to enable active reset.
"""

# Parameterized gates map to functions that produce Gate constructors.
SUPPORTED_GATES: dict[str, Union[Gate, Callable[..., Gate]]] = {
    "CCNOT": CCNOT,
    "CNOT": CNOT,
    "CSWAP": CSWAP,
    "CPHASE": cphase,
    "CPHASE00": cphase00,
    "CPHASE01": cphase01,
    "CPHASE10": cphase10,
    "CZ": CZ,
    "PHASE": phase,
    "H": H,
    "I": I,
    "ISWAP": ISWAP,
    "PSWAP": pswap,
    "RX": rx,
    "RY": ry,
    "RZ": rz,
    "S": S,
    "SWAP": SWAP,
    "T": T,
    "X": X,
    "Y": Y,
    "Z": Z,
    "XY": xy,
}


def parse_defgates(quil_str: str) -> dict[str, np.ndarray]:
    """
    Parses non-parameterized DEFGATE definitions from a Quil program string.

    This function scans through the given Quil program string and extracts
    the definitions of custom gates defined using the DEFGATE directive.
    It only supports non-parameterized gate definitions. If a parameterized
    gate definition is encountered, the function raises a ValueError.

    Args:
        quil_str (str): A string representation of a Quil program containing
                        one or more DEFGATE definitions.

    Returns:
        dict: A dictionary where each key is the name of a custom gate and
              each value is a numpy array representing the gate's unitary matrix.

    Raises:
        UnsupportedQuilInstruction: If a parameterized DEFGATE definition is encountered.
    """
    defgates = {}
    lines = quil_str.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("DEFGATE"):
            gate_name = line.split()[1]
            # Check for parameters and raise an exception if found
            if "(" in gate_name or ")" in gate_name:
                raise UnsupportedQuilInstruction("Parameterized DEFGATEs are not supported.")

            gate_name = gate_name.split(":")[0]  # Extract the gate name
            matrix_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith("DEFGATE"):
                # Split the line by comma and whitespace, then strip each element
                matrix_elements = [elem.strip() for elem in lines[i].split(",")]
                matrix_lines.append(matrix_elements)
                i += 1
            # Convert the string elements to floats
            matrix = np.array([[float(element) for element in row] for row in matrix_lines])
            defgates[gate_name] = matrix
        else:
            i += 1
    return defgates


def circuit_from_quil(quil: str) -> Circuit:
    """Convert a Quil program to a Cirq Circuit.

    Args:
        quil: The Quil program to convert.

    Returns:
        A Cirq Circuit generated from the Quil program.

    Raises:
        UnsupportedQuilInstruction: Cirq does not support the specified Quil instruction.
        UndefinedQuilGate: Cirq does not support the specified Quil gate.

    References:
        https://github.com/rigetti/pyquil
    """
    circuit = Circuit()
    defined_gates = SUPPORTED_GATES.copy()
    instructions = Program(quil).instructions

    defgates = parse_defgates(quil)

    # Add the parsed DefGates to defined_gates
    for gate_name, matrix in defgates.items():
        defined_gates[gate_name] = MatrixGate(matrix)

    for inst in instructions:
        # Pass when encountering a DECLARE.
        if isinstance(inst, Declare):
            pass

        # Convert pyQuil gates to Cirq operations.
        elif isinstance(inst, PyQuilGate):
            quil_gate_name = inst.name
            quil_gate_params = inst.params
            line_qubits = list(LineQubit(q.index) for q in inst.qubits)
            if quil_gate_name not in defined_gates:
                raise UndefinedQuilGate(f"Quil gate {quil_gate_name} not supported in Cirq.")
            cirq_gate_fn = defined_gates[quil_gate_name]
            if quil_gate_params:
                circuit += cast(Callable[..., Gate], cirq_gate_fn)(*quil_gate_params)(*line_qubits)
            else:
                circuit += cirq_gate_fn(*line_qubits)

        # Convert pyQuil MEASURE operations to Cirq MeasurementGate objects.
        elif isinstance(inst, PyQuilMeasurement):
            line_qubit = LineQubit(inst.qubit.index)
            if inst.classical_reg is None:
                raise UnsupportedQuilInstruction(
                    f"Quil measurement {inst} without classical register "
                    f"not currently supported in Cirq."
                )
            quil_memory_reference = inst.classical_reg.out()
            circuit += MeasurementGate(1, key=quil_memory_reference)(line_qubit)

        # Raise a targeted error when encountering a PRAGMA.
        elif isinstance(inst, Pragma):
            raise UnsupportedQuilInstruction(PRAGMA_ERROR)

        # Raise a targeted error when encountering a RESET.
        elif isinstance(inst, (Reset, ResetQubit)):
            raise UnsupportedQuilInstruction(RESET_ERROR)

        # Raise a general error when encountering an unconsidered type.
        else:
            raise UnsupportedQuilInstruction(
                f"Quil instruction {inst} of type {type(inst)} not currently supported in Cirq."
            )

    return circuit
