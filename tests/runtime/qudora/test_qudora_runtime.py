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
Unit tests for the QUDORA runtime module

"""

import pytest

from qbraid.runtime.qudora import QUDORABackend

qasm3_bell = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c[0] = measure q[0];
c[1] = measure q[1];
"""

qasm2_bell = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""

qasm2_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
swap q[0],q[1];
"""

qasm3_str = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
z q[0];
"""

qasm2_kirin_str = """
KIRIN {cf,func,py.ilist,qasm2.core,qasm2.expr,qasm2.glob,qasm2.indexing,qasm2.inline,qasm2.noise,qasm2.parallel,qasm2.uop};
include "qelib1.inc";
qreg qreg[4];
CX qreg[0], qreg[1];
reset qreg[0];
parallel.CZ {
  qreg[0], qreg[2];
  qreg[1], qreg[3];
}
"""


def test_process_valid_qasm2_input():
    """Test that the process_qasm_input method correctly processes QASM2 input"""
    run_input = [qasm2_str, qasm2_bell]
    language, input_data = QUDORABackend._process_qasm_input(run_input)
    assert language == "OpenQASM2"
    assert input_data == [qasm2_str, qasm2_bell]


def test_process_valid_qasm3_input():
    """Test that the process_qasm_input method correctly processes QASM3 input"""
    run_input = [qasm3_str, qasm3_bell]
    language, input_data = QUDORABackend._process_qasm_input(run_input)
    assert language == "OpenQASM3"
    assert input_data == [qasm3_str, qasm3_bell]


def test_process_valid_qasm_input_mixed_types():
    """Test that the process_qasm_input method correctly processes mixed QASM input"""
    run_input = [qasm2_bell, qasm3_bell]
    language, input_data = QUDORABackend._process_qasm_input(run_input)
    assert language == "OpenQASM3"
    assert all(program.strip() == qasm3_bell.strip() for program in input_data)


def test_process_invalid_qasm_input_mixed_types():
    """Test that the process_qasm_input method raises a ValueError for mixed invalid QASM input"""
    run_input = [qasm2_kirin_str, qasm3_bell]
    with pytest.raises(ValueError) as exc_info:
        QUDORABackend._process_qasm_input(run_input)
    assert "All input programs must be of the same type." in str(exc_info.value)


def test_process_invalid_qasm_single_input():
    """Test that the process_qasm_input method raises a ValueError for single invalid QASM input"""
    run_input = [qasm2_kirin_str]
    with pytest.raises(ValueError) as exc_info:
        QUDORABackend._process_qasm_input(run_input)
    assert "Program type not recognized. Must be 'qasm2' or 'qasm3'." in str(exc_info.value)
