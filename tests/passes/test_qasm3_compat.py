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

from qbraid.passes.qasm3.compat import (
    add_stdgates_include,
    has_redundant_parentheses,
    insert_gate_def,
    normalize_qasm_gate_params,
    remove_stdgates_include,
    replace_gate_name,
    simplify_parentheses_in_qasm,
)
from qbraid.passes.qasm3.format import _remove_empty_lines


@pytest.mark.parametrize(
    "qasm3_str_pi, qasm3_str_decimal",
    [
        (
            """
        OPENQASM 3;
        qubit[2] q;
        h q[0];
        rx(pi / 4) q[0];
        ry(2*pi) q[0];
        rz(3 * pi/4) q[0];
        cry(pi/4/2) q[0], q[1];
        """,
            """
        OPENQASM 3;
        qubit[2] q;
        h q[0];
        rx(0.7853981633974483) q[0];
        ry(6.283185307179586) q[0];
        rz(2.356194490192345) q[0];
        cry(0.39269908169872414) q[0], q[1];
        """,
        ),
    ],
)
def test_convert_pi_to_decimal(qasm3_str_pi, qasm3_str_decimal):
    """Test converting pi symbol to decimal in qasm3 string"""
    qasm_out = normalize_qasm_gate_params(qasm3_str_pi)
    assert qasm_out == qasm3_str_decimal


def test_replace_gate_name_normal():
    """Test replacing gate name in qasm string"""
    qasm = "cnot q[0], q[1];"
    assert replace_gate_name(qasm, "cnot", "cx") == "cx q[0], q[1];"


def test_replace_gate_name_forced():
    """Test forced replace of gate name in qasm string"""
    qasm = "x q[0];"
    assert replace_gate_name(qasm, "x", "pauli_x", force_replace=True) == "pauli_x q[0];"


def test_replace_gate_name_with_parameters():
    """Test replacing gate name with parameters in qasm string"""
    qasm = "p(3.14) q[0];"
    assert replace_gate_name(qasm, "p", "phaseshift") == "phaseshift(3.14) q[0];"


def test_no_replacement_when_not_matched():
    """Test not replacing gate name in qasm string when not matched"""
    qasm = "cnot q[0], q[1];"
    assert replace_gate_name(qasm, "cnot", "notvalid", force_replace=False) == "cnot q[0], q[1];"


def test_force_replace_when_not_matched():
    """Test force replacing gate name in qasm string when not matched"""
    qasm = "cnot q[0], q[1];"
    assert replace_gate_name(qasm, "cnot", "notvalid", force_replace=True) == "notvalid q[0], q[1];"


def test_replace_non_parameterized_with_parameterized():
    """Test replacing non-parameterized gates with parameterized gates in qasm string"""
    qasm = "v q[0];"
    assert replace_gate_name(qasm, "v", "sx") == "sx q[0];"
    qasm = "ti q[0];"
    assert replace_gate_name(qasm, "ti", "tdg") == "tdg q[0];"


@pytest.mark.parametrize(
    "qasm3_in, qasm3_out",
    [
        (
            """
        OPENQASM 3.0;

        qubit[2] q;

        cnot q[0], q[1];
        sx q[0];
        p(3.14) q[1];
        cp(3.14) q[0], q[1];
        """,
            """
        OPENQASM 3.0;

        qubit[2] q;

        cx q[0], q[1];
        v q[0];
        phaseshift(3.14) q[1];
        cphaseshift(3.14) q[0], q[1];
        """,
        ),
    ],
)
def test_parameterized_replacement(qasm3_in, qasm3_out):
    """Test replacing non-parameterized gates with parameterized gates in qasm3 string"""
    qasm3 = replace_gate_name(qasm3_in, "cnot", "cx")
    qasm3 = replace_gate_name(qasm3, "sx", "v")
    qasm3 = replace_gate_name(qasm3, "p", "phaseshift")
    qasm3 = replace_gate_name(qasm3, "cp", "cphaseshift")
    assert qasm3 == qasm3_out


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


def test_bad_insert_gate_def():
    """Test inserting gate definition with invalid qasm3 string"""
    qasm3 = ""
    with pytest.raises(ValueError):
        insert_gate_def(qasm3, "bad_gate")


def test_simplify_parentheses_in_qasm():
    """Test simplifying parentheses in qasm string"""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cry((0.7853981633974483)) q[0], q[1];
ry(-(0.39269908169872414)) q[1];
"""
    expected = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cry(0.7853981633974483) q[0], q[1];
ry(-0.39269908169872414) q[1];
"""
    assert simplify_parentheses_in_qasm(qasm).strip() == expected.strip()


@pytest.mark.parametrize(
    "qasm_input, expected_result",
    [
        (
            """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cry((0.39269908169872414)) q[0], q[1];
    """,
            True,
        ),
        (
            """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    crx(-(0.39269908169872414)) q[0], q[1];
    """,
            True,
        ),
        (
            """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    rx(0.7853981633974483) q[0];
    ry(6.283185307179586) q[0];
    rz(2.356194490192345) q[0];
    cry(0.39269908169872414) q[0], q[1];
    """,
            False,
        ),
    ],
)
def test_has_redundant_parentheses(qasm_input, expected_result):
    """Test checking for redundant parentheses in QASM string."""
    assert has_redundant_parentheses(qasm_input) == expected_result
