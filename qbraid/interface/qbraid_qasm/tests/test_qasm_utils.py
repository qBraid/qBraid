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
Unit tests for OpenQASM 2 utility functions.

"""

import pytest

from qbraid.interface.qbraid_qasm.circuits import qasm2_bell, qasm2_raw_shared15, qasm2_shared15
from qbraid.interface.qbraid_qasm.tools import qasm_depth, qasm_num_qubits, qasm_qubits


def test_qasm_qubits():
    """Test getting QASM qubits"""

    assert qasm_qubits(qasm2_bell()) == ["qreg q[2];"]
    assert qasm_qubits(qasm2_shared15()) == ["qreg q[4];"]


def test_qasm_num_qubits():
    """Test calculating number of qubits in qasm2 circuit"""
    assert qasm_num_qubits(qasm2_bell()) == 2
    assert qasm_num_qubits(qasm2_shared15()) == 4


def test_qasm_depth():
    """Test calculating qasm depth of qasm2 circuit"""
    assert qasm_depth(qasm2_bell()) == 2
    assert qasm_depth(qasm2_shared15()) == 11
    assert qasm_depth(qasm2_raw_shared15()) == 22


@pytest.mark.skip(reason="Not implemented")
@pytest.mark.parametrize(
    "qasm_str, expected_depth",
    [
        (
            """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c0[1];
    creg c1[1];
    h q[0];
    h q[1];
    measure q[0] -> c0[0];
    if(c0==0) x q[1];
    """,
            3,
        ),
        (
            """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c0[1];
    creg c1[1];
    h q[0];
    h q[1];
    measure q[0] -> c0[0];
    if(c0==0) x q[1];
    if(c0==0) measure q[1] -> c1[0];
    """,
            4,
        ),
    ],
)
def test_qasm_depth_if_statement(qasm_str, expected_depth):
    """Test calculating qasm depth with program containing if statement"""
    assert qasm_depth(qasm_str) == expected_depth
