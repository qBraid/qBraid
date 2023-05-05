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
Module for converting QASM code to Amazon Braket code

"""

from typing import Optional

# pylint: disable=unspecified-encoding,consider-using-with

python_code = [
    "import numpy as np\n",
    "from braket.circuits import Circuit\n\n",
    "circuit = Circuit()\n",
]


def u3_decomposition(theta, phi, lam, q):
    """Decompose QASM u3 into gates supported by Amazon Braket"""
    return f"""
# u3
circuit.rz({q}, {phi})
circuit.rx({q}, -np.pi/2)
circuit.rz({q}, {theta})
circuit.rx({q}, np.pi/2)
circuit.rz({q}, {lam})
"""


def qasm_line_to_braket(op, args):
    """Convert line of QASM code to Amazon Braket."""
    if op in ["h", "x", "y", "z", "s", "t", "sx", "sxdg", "sdg", "tdg"]:
        q = args[0][2]
        if op in ["sx", "sxdg", "sdg", "tdg"]:
            op = op.replace("sx", "v")
            op = op.replace("dg", "i")
        return f"circuit.{op}({q})\n"
    if op[:2] in ["rx", "ry", "rz"]:
        q = args[0][2]
        op = op.replace("pi", "np.pi")
        return f"circuit.{op[:3]}{q}, {op[3:]}\n"
    if op in ["cx", "swap"]:
        qs = args[0].split(",")
        q0 = qs[0][2]
        q1 = qs[1][2]
        if op == "cx":
            op = "cnot"
        return f"circuit.{op}({q0}, {q1})\n"
    if op[0:2] == "u3":
        q = args[0][2]
        op = op.replace("pi", "np.pi")
        theta, phi, lam = op[3:-1].split(",")
        return u3_decomposition(theta, phi, lam, q)

    return ""


def qasm_to_braket_code(
    qasm_file: Optional[str] = None,
    qasm_str: Optional[str] = None,
    output_file: Optional[str] = None,
    print_circuit: bool = False,
):
    """Convert QASM string/file to Python file with circuit implemented using Amazon Braket.

    Args:
        qasm_file: path to input .qasm file
        qasm_str: input raw QASM string
        output_file: path to output Python file
        print_circuit: If True, adds line to print Amazon Braket circuit

    Returns:
        None

    """
    if qasm_file is not None:
        # read in qasm file
        qasm_in = open(qasm_file, "r")
        qasm_code = qasm_in.readlines()
    elif qasm_str is not None:
        qasm_code = qasm_str.split("\n")
    else:
        raise ValueError("Must specify a value for qasm_str or qasm_file")

    if output_file is None:
        output_file = "braket_out.py"

    for line in qasm_code:
        expr = line.strip().split(" ")
        op = expr[0]
        args = expr[1:]
        py_line = qasm_line_to_braket(op, args)
        if py_line != "":
            python_code.append(py_line)

    if print_circuit:
        python_code.append("\nprint(circuit)\n")

    #  writing to file
    braket_out = open(output_file, "w")
    braket_out.writelines(python_code)
    braket_out.close()
