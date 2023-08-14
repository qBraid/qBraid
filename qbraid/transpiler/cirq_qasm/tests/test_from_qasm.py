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
Unit tests for QASM preprocessing functions

"""

import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.interface.qbraid_qasm.qasm_preprocess import convert_to_supported_qasm
from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm

qasm_0 = """OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(-pi/4) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
gate rzx_6320157840(param0) q0,q1 { h q1; cx q0,q1; rz(2.3200048200765524) q1; cx q0,q1; h q1; }
qreg q[4];
cry(5.518945082555831) q[0],q[1];
u(5.75740842861076,5.870881397684582,1.8535618384181967) q[2];
ecr q[3],q[0];
rzx_6320157840(2.3200048200765524) q[2],q[1];
rccx q[1],q[2],q[3];
csx q[0],q[1];
rxx(5.603791034636421) q[2],q[0];
"""

qasm_1 = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[5];
rccx q[1],q[2],q[0];
cu(5.64,3.60,3.73, 5.68) q[1],q[0];
c3x q[1],q[3],q[0],q[2];
c3sqrtx q[3],q[1],q[2],q[0];
c4x q[2],q[0],q[1],q[4],q[3];
rc3x q[1],q[2],q[0],q[3];
"""

qasm_lst = [qasm_0, qasm_1]

def strings_equal(s1, s2):
    """Check if two strings are equal, ignoring spaces and newlines."""
    s1_clean = s1.replace(" ", "").replace("\n", "")
    s2_clean = s2.replace(" ", "").replace("\n", "")
    return s1_clean == s2_clean


@pytest.mark.parametrize("qasm_str", qasm_lst)
def test_preprocess_qasm(qasm_str):
    """Test converting qasm string to format supported by Cirq parser"""
    qiskit_circuit = QuantumCircuit().from_qasm_str(qasm_str)
    supported_qasm = convert_to_supported_qasm(qasm_str)
    cirq_circuit = from_qasm(supported_qasm)
    cirq_circuit_compat = _convert_to_line_qubits(cirq_circuit)
    assert circuits_allclose(cirq_circuit_compat, qiskit_circuit)