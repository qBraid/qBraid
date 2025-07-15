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
import re
import textwrap

import pytest

from qbraid.passes.qasm.compat import (
    _evaluate_expression,
    _normalize_case_insensitive_map,
    add_stdgates_include,
    convert_qasm_pi_to_decimal,
    has_redundant_parentheses,
    insert_gate_def,
    normalize_qasm_gate_params,
    remove_stdgates_include,
    replace_gate_names,
    simplify_parentheses_in_qasm,
)


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

    def _remove_empty_lines(input_string: str) -> str:
        """Removes all empty lines from the provided string."""
        return "\n".join(line for line in input_string.split("\n") if line.strip())

    test_with = _remove_empty_lines(add_stdgates_include(qasm3_without))
    expected_with = _remove_empty_lines(qasm3_with)

    test_without = _remove_empty_lines(remove_stdgates_include(qasm3_with))
    expected_without = _remove_empty_lines(qasm3_without)

    test_redundant = add_stdgates_include(qasm3_with)

    assert test_with == expected_with
    assert test_without == expected_without
    assert test_redundant == qasm3_with


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


@pytest.mark.parametrize(
    "qasm_body, old_gate, new_gate, expected_body",
    [
        (
            "cnot q[0], q[1];",
            "cnot",
            "cx",
            "cx q[0], q[1];",
        ),
        (
            "cnot q[0], q[1];",
            "cnot",
            "custom",
            "custom q[0], q[1];",
        ),
        (
            "cnot q[0], q[1];",
            "notmatched",
            "cx",
            "cnot q[0], q[1];",
        ),
    ],
)
def test_replace_gate_name_qubit_2(qasm_body, old_gate, new_gate, expected_body):
    """Test replacing gate names in QASM strings for two qubit gates."""
    qasm = f"OPENQASM 3; qubit[2] q; {qasm_body}"
    expected_output = f"OPENQASM 3;\nqubit[2] q;\n{expected_body}\n"
    assert replace_gate_names(qasm, {old_gate: new_gate}) == expected_output

    qasm2 = f"OPENQASM 2; qreg q[2]; {qasm_body}"
    qasm2_expected_output = f"OPENQASM 2;\nqreg q[2];\n{expected_body}\n"
    assert replace_gate_names(qasm2, {old_gate: new_gate}) == qasm2_expected_output


@pytest.mark.parametrize(
    "qasm_body, old_gate, new_gate, expected_body",
    [
        (
            "x q[0];",
            "x",
            "pauli_x",
            "pauli_x q[0];",
        ),
        (
            "p(3.14) q[0];",
            "p",
            "phaseshift",
            "phaseshift(3.14) q[0];",
        ),
        (
            "v q[0];",
            "v",
            "sx",
            "sx q[0];",
        ),
        (
            "ti q[0];",
            "ti",
            "tdg",
            "tdg q[0];",
        ),
    ],
)
def test_replace_gate_name_qubit_1(qasm_body, old_gate, new_gate, expected_body):
    """Test replacing gate names in QASM strings for one qubit gates."""
    qasm3 = f"OPENQASM 3; qubit[1] q; {qasm_body}"
    qasm3_expected_output = f"OPENQASM 3;\nqubit[1] q;\n{expected_body}\n"
    assert replace_gate_names(qasm3, {old_gate: new_gate}) == qasm3_expected_output

    qasm2 = f"OPENQASM 2; qreg q[1]; {qasm_body}"
    qasm2_expected_output = f"OPENQASM 2;\nqreg q[1];\n{expected_body}\n"
    assert replace_gate_names(qasm2, {old_gate: new_gate}) == qasm2_expected_output


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
    replacements = {"cnot": "cx", "sx": "v", "p": "phaseshift", "cp": "cphaseshift"}
    qasm3 = replace_gate_names(qasm3_in, replacements)
    qasm3 = textwrap.dedent(qasm3).strip()
    qasm3_out = textwrap.dedent(qasm3_out).strip()
    assert qasm3 == qasm3_out


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


def test_evaluate_expression_error():
    """Test simplifying arithmetic expression with error in qasm string"""
    qasm_str = "gate str(gate_name)(a, b) q {U(1*) q;}"
    match = re.search(r"\(([0-9+\-*/. ]+)\)", qasm_str)

    assert _evaluate_expression(match) == "(1*)"


def test_convert_qasm_pi_to_decimal_omits_gpi_gate():
    """Test converting pi symbol to decimal in qasm string with gpi and gpi2 gates."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    gpi(0) q[0];
    gpi2(0) q[1];
    cry(pi) q[0], q[1];
    """

    expected = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    gpi(0) q[0];
    gpi2(0) q[1];
    cry(3.141592653589793) q[0], q[1];
    """
    assert convert_qasm_pi_to_decimal(qasm) == expected


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


def test_forced_gate_def_insertion():
    """Test inserting gate definition with force_insert=True."""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cnot q[0], q[1];
    """

    expected = """
OPENQASM 3.0;
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
include "stdgates.inc";
qubit[2] q;
h q[0];
cnot q[0], q[1];
    """
    assert insert_gate_def(qasm, "iswap", force_insert=True) == expected


def test_gate_def_insertion_with_include():
    """Test inserting gate definition when include statement is present (include_idx case)."""
    qasm = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
h q[0];
sxdg q[0];
    """

    expected = """
OPENQASM 3.0;
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
include "stdgates.inc";
qubit[1] q;
h q[0];
sxdg q[0];
    """
    result = insert_gate_def(qasm, "sxdg")
    assert result == expected


def test_gate_def_insertion_without_include():
    """Test inserting gate definition when no include statement is present (openqasm_idx case)."""
    qasm = """
OPENQASM 3.0;
qubit[1] q;
h q[0];
    """

    expected = """
OPENQASM 3.0;
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
qubit[1] q;
h q[0];
    """
    result = insert_gate_def(qasm, "sxdg", force_insert=True)
    assert result == expected


def test_normalize_case_insensitive_map():
    """Test normalizing a case-insensitive map."""
    test_map = {"a": 1, "B": 2, "c": 3}
    expected_map = {"a": 1, "b": 2, "c": 3}
    assert _normalize_case_insensitive_map(test_map) == expected_map


def test_normalize_case_insensitive_map_raises_error():
    """Test normalizing a case-insensitive map raises an error if keys are not unique."""
    test_map = {"a": 1, "A": 2}
    with pytest.raises(ValueError):
        _normalize_case_insensitive_map(test_map)
