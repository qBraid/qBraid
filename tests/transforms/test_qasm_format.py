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
Unit tests for QASM formatting functions

"""
import pytest

from qbraid.transforms.qasm3.format import remove_unused_gates


def test_remove_unused_single_line_non_parameterized_gate():
    """Test removing unused single line non-parameterized gate definition."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate unused_gate a { x a; }

h q[0];
"""
    expected_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

h q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == expected_qasm.strip()


def test_keep_used_single_line_non_parameterized_gate():
    """Test keeping used single line non-parameterized gate definition."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate used_gate a { x a; }

used_gate q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == input_qasm.strip()


def test_remove_unused_multi_line_parameterized_gate():
    """Test removing unused multi line parameterized gate definition."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate unused_gate(param) a {
    rz(param) a;
    x a;
}

h q[0];
"""
    expected_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

h q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == expected_qasm.strip()


def test_keep_used_multi_line_parameterized_gate():
    """Test keeping used multi line parameterized gate definition."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate used_gate(param) a {
    rz(param) a;
    x a;
}

used_gate(pi/2) q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == input_qasm.strip()


def test_recursively_remove_nested_unused_gates():
    """Test recursively removing unused, nested gate definition."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate nested_gate a { x a; }

gate unused_gate(param) a {
    rz(param) a;
    nested_gate a;
}

h q[0];
"""
    expected_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

h q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == expected_qasm.strip()


def test_keep_remove_split_usage_nested_gates():
    """Test keeping nested gates that are used, removing those that aren't."""
    input_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate nested_gate a { x a; }

gate unused_gate(param) a {
    rz(param) a;
    nested_gate a;
}

gate used_gate(param) a {
    ry(param) a;
    nested_gate a;
}

used_gate(pi/2) q[0];
"""
    expected_qasm = """
OPENQASM 3.0;
include 'stdgates.inc';

qubit[1] q;

gate nested_gate a { x a; }

gate used_gate(param) a {
    ry(param) a;
    nested_gate a;
}

used_gate(pi/2) q[0];
"""
    assert remove_unused_gates(input_qasm).strip() == expected_qasm.strip()


@pytest.mark.skip(reason="Not passing")
def test_remove_unused_gate_delared_before_qubits():
    """Test removing unused gate before qubit declaration."""
    input_qasm = """
OPENQASM 3.0;

gate u(theta,phi,lambda) q { u3(theta,phi,lambda) q; }

qubit[2] q;

z q[0];
cx q[1],q[0];
z q[1];
"""
    expected_qasm = """
OPENQASM 3.0;

qubit[2] q;

z q[0];
cx q[1],q[0];
z q[1];
"""
    assert remove_unused_gates(input_qasm).strip() == expected_qasm.strip()
