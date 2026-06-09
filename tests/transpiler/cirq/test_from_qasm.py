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

"""
Unit tests for QASM preprocessing functions

"""

import cirq
import pyqasm
import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.programs import load_program
from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq
from qbraid.transpiler.conversions.qasm3 import qasm3_to_cirq

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
rzx(5.603791034636421) q[2],q[0];
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


def _test_qasm_preprocess(qasm_str):
    """Test converting qasm string to format supported by Cirq parser"""
    qiskit_circuit = QuantumCircuit().from_qasm_str(qasm_str)
    qasm_module = pyqasm.loads(qasm_str)
    qasm_module.unroll()
    supported_qasm = pyqasm.dumps(qasm_module)
    cirq_circuit = qasm2_to_cirq(supported_qasm)
    qprogram = load_program(cirq_circuit)
    qprogram._convert_to_line_qubits()
    cirq_circuit_compat = qprogram.program
    assert circuits_allclose(cirq_circuit_compat, qiskit_circuit)


def test_preprocess_qasm_0():
    """Test converting qasm string to format supported by Cirq parser"""
    _test_qasm_preprocess(qasm_0)


@pytest.mark.skip(reason="Mapping not implemented yet for complex quantum gates")
def test_preprocess_qasm_1():
    """Test converting qasm string to format supported by Cirq parser"""
    _test_qasm_preprocess(qasm_1)


def test_qasm2_to_cirq_with_conditionals():
    """Test end-to-end conversion of QASM 2 with if statements."""
    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c0[1];
creg c1[1];
h q[1];
cx q[1],q[2];
cx q[0],q[1];
h q[0];
measure q[0] -> c0[0];
measure q[1] -> c1[0];
if(c0==1) z q[2];
if(c1==1) x q[2];
"""
    circuit = qasm2_to_cirq(qasm)
    assert isinstance(circuit, cirq.Circuit)

    ops_list = list(circuit.all_operations())
    classically_controlled = [
        op for op in ops_list if isinstance(op, cirq.ClassicallyControlledOperation)
    ]
    assert len(classically_controlled) == 2


def test_qasm2_to_cirq_teleportation():
    """Test full quantum teleportation circuit with conditionals."""
    qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c0[1];
creg c1[1];
creg c2[1];
gate post q { }
u3(0.3,0.2,0.1) q[0];
h q[1];
cx q[1],q[2];
barrier q;
cx q[0],q[1];
h q[0];
measure q[0] -> c0[0];
measure q[1] -> c1[0];
if(c0==1) z q[2];
if(c1==1) x q[2];
post q[2];
measure q[2] -> c2[0];
"""
    circuit = qasm2_to_cirq(qasm)
    assert isinstance(circuit, cirq.Circuit)

    ops_list = list(circuit.all_operations())
    classically_controlled = [
        op for op in ops_list if isinstance(op, cirq.ClassicallyControlledOperation)
    ]
    assert len(classically_controlled) == 2

    measurements = [op for op in ops_list if isinstance(op.gate, cirq.MeasurementGate)]
    assert len(measurements) == 3


def test_qasm3_to_cirq_with_conditionals():
    """Test QASM 3 to Cirq conversion with if statements."""
    qasm = """OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[1] c0;
bit[1] c1;
h q[1];
cx q[1], q[2];
cx q[0], q[1];
h q[0];
c0[0] = measure q[0];
c1[0] = measure q[1];
if (c0 == 1) z q[2];
if (c1 == 1) x q[2];
"""
    circuit = qasm3_to_cirq(qasm)
    assert isinstance(circuit, cirq.Circuit)

    ops_list = list(circuit.all_operations())
    classically_controlled = [
        op for op in ops_list if isinstance(op, cirq.ClassicallyControlledOperation)
    ]
    assert len(classically_controlled) == 2


def test_qasm3_to_cirq_teleportation():
    """Test full QASM 3 quantum teleportation circuit with conditionals."""
    qasm = """OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
bit[1] c0;
bit[1] c1;
bit[1] c2;
gate post q { }
U(0.3, 0.2, 0.1) q[0];
h q[1];
cnot q[1], q[2];
cnot q[0], q[1];
h q[0];
c0[0] = measure q[0];
c1[0] = measure q[1];
if (c0 == 1) z q[2];
if (c1 == 1) x q[2];
post q[2];
c2[0] = measure q[2];
"""
    circuit = qasm3_to_cirq(qasm)
    assert isinstance(circuit, cirq.Circuit)

    ops_list = list(circuit.all_operations())
    classically_controlled = [
        op for op in ops_list if isinstance(op, cirq.ClassicallyControlledOperation)
    ]
    assert len(classically_controlled) == 2

    measurements = [op for op in ops_list if isinstance(op.gate, cirq.MeasurementGate)]
    assert len(measurements) == 3


def test_qasm3_to_cirq_without_conditionals():
    """Test QASM 3 to Cirq conversion without conditionals still works."""
    qasm = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cnot q[0], q[1];
"""
    circuit = qasm3_to_cirq(qasm)
    assert isinstance(circuit, cirq.Circuit)
    assert len(list(circuit.all_operations())) == 2
