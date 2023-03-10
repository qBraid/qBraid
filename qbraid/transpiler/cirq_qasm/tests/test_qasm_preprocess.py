# Copyright 2023 qBraid
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

"""
Unit tests for QASM preprocessing functions

"""

import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm
from qbraid.transpiler.cirq_qasm.qasm_preprocess import convert_to_supported_qasm

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

qasm_lst = [qasm_0]


@pytest.mark.parametrize("qasm_str", qasm_lst)
def test_preprocess_qasm(qasm_str):
    qiskit_circuit = QuantumCircuit().from_qasm_str(qasm_str)
    supported_qasm = convert_to_supported_qasm(qasm_str)
    print(qasm_str)
    print()
    print(supported_qasm)
    cirq_circuit = from_qasm(supported_qasm)
    cirq_circuit_compat = _convert_to_line_qubits(cirq_circuit, rev_qubits=True)
    assert circuits_allclose(cirq_circuit_compat, qiskit_circuit)
