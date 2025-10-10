# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=expression-not-assigned
"""
Unit tests for OpenQASM2 to pyqpanda3 transpilation.

"""

from __future__ import annotations

import numpy as np
import pytest

from qbraid import transpile
from qbraid.interface import circuits_allclose

pyqpanda3 = pytest.importorskip("pyqpanda3")


def test_openqasm2_to_pyqpanda3():
    """Test converting an OpenQASM2 program to a pyqpanda3 QProg"""

    qasm2_str_in = """
    OPENQASM 2.0;
    include "stdgates.inc";
    // comment
    qubit[1] q;

    h q[0];
    x q[0];
    y q[0];
    """
    qprog = transpile(qasm2_str_in, target="pyqpanda3")

    expected = pyqpanda3.core.QProg()
    expected << pyqpanda3.core.H(0) << pyqpanda3.core.X(0) << pyqpanda3.core.Y(0)

    # pylint thinks .ndarray() has an extra argument, so disabling for the test
    # pylint: disable=no-value-for-parameter
    u_obs = pyqpanda3.quantum_info.Unitary(qprog.to_circuit()).ndarray()
    u_expected = pyqpanda3.quantum_info.Unitary(expected.to_circuit()).ndarray()
    assert np.allclose(u_obs, u_expected)


# Skip test as pyqpanda3 generates qasm with a creg of size 0 even
# though there are no classical bits in the circuit. pyqasm, which parses
# this output for circuits_allclose, errors that creg size must be > 0.
@pytest.mark.skip
def test_pyqpanda3_to_openqasm2():
    """Test converting a pyqpanda3 QProg to OpenQASM2"""

    prog = pyqpanda3.core.QProg()
    prog << pyqpanda3.core.RX(0, 3.1415926) << pyqpanda3.core.CNOT(0, 2)

    expected = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    rx(3.14159260) q[0];
    cx q[0],q[2];
    """

    res = transpile(prog, target="qasm2")
    assert circuits_allclose(res, expected)


# Until the above is supported, compare the QASM strings directly
def test_pyqpanda3_to_openqasm2_str_cmp():
    """Test converting a pyqpanda3 QProg to OpenQASM2"""

    prog = pyqpanda3.core.QProg()
    prog << pyqpanda3.core.RX(0, 3.1415926) << pyqpanda3.core.CNOT(0, 2)

    expected = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg c[0];
    rx(3.14159260) q[0];
    cx q[0],q[2];
    """

    res = transpile(prog, target="qasm2")

    # Normalize whitespace for comparison
    res_normalized = "".join(res.split())
    expected_normalized = "".join(expected.split())
    assert res_normalized == expected_normalized
