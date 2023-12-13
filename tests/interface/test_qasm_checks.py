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
Unit tests for verifying OpenQASM programs

"""

import pytest

from qbraid.exceptions import QasmError
from qbraid.interface.qasm_checks import get_qasm_version

QASM_BELL_DATA = [
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
        """,
        "qasm2",
    ),
    (
        """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
        """,
        "qasm3",
    ),
    (
        """
OPENQASM 3.0;
bit[2] __bits__;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
__bits__[0] = measure __qubits__[0];
__bits__[1] = measure __qubits__[1];
        """,
        "qasm3",
    ),
]

QASM_ERROR_DATA = [
    """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0;
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];

        """,
    """
OPENQASM 3.0;
include "stdgates.inc";
bit c[2];
qubit q[2];
h q[0]
cx q[0], q[1];
measure q -> c;
        """,
]


@pytest.mark.parametrize("qasm_str, expected_version", QASM_BELL_DATA)
def test_get_qasm_version(qasm_str, expected_version):
    """Test getting QASM version"""
    assert get_qasm_version(qasm_str) == expected_version


@pytest.mark.parametrize("qasm_str", QASM_ERROR_DATA)
def test_get_qasm_version_error(qasm_str):
    """Test getting QASM version"""
    with pytest.raises(QasmError):
        get_qasm_version(qasm_str)
