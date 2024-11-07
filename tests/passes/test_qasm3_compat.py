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
Unit tests for QASM preprocessing functions

"""
import pytest

from qbraid.passes.qasm.compat import (
    add_stdgates_include,
    convert_qasm_pi_to_decimal,
    remove_stdgates_include,
)
from qbraid.passes.qasm.format import _remove_empty_lines


@pytest.mark.skip(reason="move to pyqasm")
@pytest.mark.parametrize(
    "qasm3_without, qasm3_with",
    [
        (
            """
OPENQASM 3;
qubit[1] q;
h q[0];
ry(pi/4) q[0];
        """,
            """
OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
h q[0];
ry(pi/4) q[0];
        """,
        ),
    ],
)
def test_add_stdgates_include(qasm3_without, qasm3_with):
    """Test adding stdgates include to OpenQASM 3.0 string"""
    test_with = _remove_empty_lines(add_stdgates_include(qasm3_without))
    expected_with = _remove_empty_lines(qasm3_with)

    test_without = _remove_empty_lines(remove_stdgates_include(qasm3_with))
    expected_without = _remove_empty_lines(qasm3_without)

    test_redundant = add_stdgates_include(qasm3_with)

    assert test_with == expected_with
    assert test_without == expected_without
    assert test_redundant == qasm3_with


@pytest.mark.skip(reason="move to pyqasm")
def test_convert_qasm_pi_to_decimal_gpi2_iso():
    """Test converting pi symbol to decimal in qasm string with gpi2 gate on its own."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    gpi2(pi/4) q[0];
    """

    expected = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    gpi2(0.7853981633974483) q[0];
    """
    assert convert_qasm_pi_to_decimal(qasm) == expected


@pytest.mark.skip(reason="move to pyqasm")
def test_convert_qasm_pi_to_decimal_qasm3_fns_gates_vars():
    """Test converting pi symbol to decimal in a qasm3 string
    with custom functions, gates, and variables."""
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";

    gate pipe q {
        gpi(0) q;
        gpi2(pi/8) q;
    }

    const int[32] primeN = 3;
    const float[32] c = primeN*pi/4;
    qubit[3] q;

    def spiral(qubit[primeN] q_func) {
    for int i in [0:primeN-1] { pipe q_func[i]; }
    }

    spiral(q);

    ry(c) q[0];

    bit[3] result;
    result = measure q;
    """

    expected = """
    OPENQASM 3;
    include "stdgates.inc";

    gate pipe q {
        gpi(0) q;
        gpi2(0.39269908169872414) q;
    }

    const int[32] primeN = 3;
    const float[32] c = primeN*0.7853981633974483;
    qubit[3] q;

    def spiral(qubit[primeN] q_func) {
    for int i in [0:primeN-1] { pipe q_func[i]; }
    }

    spiral(q);

    ry(c) q[0];

    bit[3] result;
    result = measure q;
    """
    assert convert_qasm_pi_to_decimal(qasm) == expected


@pytest.mark.parametrize(
    "qasm_input, expected_output",
    [
        (
            """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
gpi(0) q[0];
gpi2(0) q[1];
cry(pi) q[0], q[1];""",
            """
OPENQASM 2.0;
qreg q[2];
gpi(0) q[0];
gpi2(0) q[1];
cry(pi) q[0], q[1];
            """,
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crz(pi / 4) q[0], q[1];
            """,
            """
OPENQASM 3.0;
qubit[2] q;
crz(pi / 4) q[0], q[1];
            """,
        ),
    ],
)
def test_remove_include_statements(qasm_input: str, expected_output: str):
    """Test removing include statements from QASM string."""
    assert expected_output.strip() == remove_include_statements(qasm_input).strip()
