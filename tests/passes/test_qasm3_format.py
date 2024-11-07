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

from qbraid.passes.qasm.format import remove_unused_gates


@pytest.mark.skip(reason="move to pyqasm")
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


@pytest.mark.skip(reason="move to pyqasm")
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
