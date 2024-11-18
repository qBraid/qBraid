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

from qbraid.passes.qasm.compat import insert_gate_def, replace_gate_name


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


def test_bad_insert_gate_def():
    """Test inserting gate definition with invalid qasm3 string"""
    qasm3 = ""
    with pytest.raises(ValueError):
        insert_gate_def(qasm3, "bad_gate")
