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
Unit tests for converting QASM code to Amazon Braket code

"""

import os
import sys

import pytest

from qbraid.transpiler.code.qasm_to_braket import qasm_to_braket_code

from ..._data.cirq.circuits import cirq_shared15

test_code = """
import qbraid
from qbraid.interface import convert_to_contiguous, circuits_allclose
cirq_circuit = qbraid.circuit_wrapper(circuit).transpile("cirq")
cirq_flipped = convert_to_contiguous(cirq_circuit, rev_qubits=True)
all_close = circuits_allclose(circuit, cirq_circuit)
all_close_flipped = circuits_allclose(circuit, cirq_flipped)
passed = all_close or all_close_flipped
print(passed)
"""


def test_qasm_to_braket_code_from_str(capfd):
    cirq_circuit = cirq_shared15()
    qasm_str = cirq_circuit.to_qasm()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, "_braket_out_0.py")
    if os.path.isfile(output_file):
        os.remove(output_file)
    qasm_to_braket_code(qasm_str=qasm_str, output_file=output_file)

    # write test code to output file
    braket_out = open(output_file, "a")
    braket_out.writelines(test_code)
    braket_out.close()

    os.system(f"{sys.executable} {output_file}")
    out, err = capfd.readouterr()
    assert out == "True\n"
    assert len(err) == 0
    os.remove(output_file)


def test_qasm_to_braket_code_from_file(capfd):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "shared15.qasm")
    output_file = os.path.join(current_dir, "_braket_out_1.py")
    if os.path.isfile(output_file):
        os.remove(output_file)
    qasm_to_braket_code(qasm_file=input_file, output_file=output_file)

    # write test code to output file
    braket_out = open(output_file, "a")
    braket_out.writelines(test_code)
    braket_out.close()

    os.system(f"{sys.executable} {output_file}")
    out, err = capfd.readouterr()
    assert out == "True\n"
    assert len(err) == 0
    os.remove(output_file)


def test_qasm_to_braket_code_print_circuit(capfd):
    cirq_circuit_1 = cirq_shared15()
    qasm_str_1 = cirq_circuit_1.to_qasm()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, "_braket_out_2.py")
    if os.path.isfile(output_file):
        os.remove(output_file)
    qasm_to_braket_code(qasm_str=qasm_str_1, output_file=output_file, print_circuit=True)

    os.system(f"{sys.executable} {output_file}")
    out, err = capfd.readouterr()
    assert len(out) == 4631
    assert len(err) == 0
    os.remove(output_file)


def test_qasm_to_braket_code_raises_error():
    with pytest.raises(ValueError):
        qasm_to_braket_code()
