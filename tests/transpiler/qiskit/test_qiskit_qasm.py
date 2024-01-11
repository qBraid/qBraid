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
Unit tests for converting qiskit circuits to/from OpenQASM.

"""
import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.conversions.qiskit.conversions_qasm import (
    _add_stdgates_include,
    qasm3_to_qiskit,
    qiskit_to_qasm3,
)

qasm_stdgate_data = [
    (
        """
OPENQASM 3;
qubit[1] q;
h q[0];
rypi/4) q[0];
        """,
        """
OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
h q[0];
rypi/4) q[0];
        """,
    ),
]


@pytest.mark.parametrize("qasm3_test_in, qasm3_expected_out", qasm_stdgate_data)
def test_add_stdgates_include(qasm3_test_in, qasm3_expected_out):
    """Test adding stdgates include to OpenQASM 3.0 string"""
    assert _add_stdgates_include(qasm3_test_in) == qasm3_expected_out


def test_qiskit_to_from_qasm3():
    """Test converting qiskit circuit to/from OpenQASM 3.0 string"""
    circuit_in = QuantumCircuit(2)
    circuit_in.h(0)
    circuit_in.cx(0, 1)

    qasm3_str = qiskit_to_qasm3(circuit_in)
    circuit_out = qasm3_to_qiskit(qasm3_str)
    assert circuits_allclose(circuit_in, circuit_out, strict_gphase=True)
