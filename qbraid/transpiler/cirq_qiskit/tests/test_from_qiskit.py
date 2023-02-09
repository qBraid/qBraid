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
Unit tests for converting Qiskit circuits to Cirq circuits.

"""
import numpy as np
import pytest
from qiskit import QuantumCircuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.cirq_qiskit.conversions import from_qiskit


def test_bell_state_from_qiskit():
    """Tests qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_common_gates_from_qiskit():
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.h([0, 1, 2, 3])
    qiskit_circuit.x([0, 1])
    qiskit_circuit.y(2)
    qiskit_circuit.z(3)
    qiskit_circuit.s(0)
    qiskit_circuit.sdg(1)
    qiskit_circuit.t(2)
    qiskit_circuit.tdg(3)
    qiskit_circuit.rx(np.pi / 4, 0)
    qiskit_circuit.ry(np.pi / 2, 1)
    qiskit_circuit.rz(3 * np.pi / 4, 2)
    qiskit_circuit.p(np.pi / 8, 3)
    qiskit_circuit.sx(0)
    qiskit_circuit.sxdg(1)
    qiskit_circuit.iswap(2, 3)
    qiskit_circuit.swap([0, 1], [2, 3])
    qiskit_circuit.cx(0, 1)
    qiskit_circuit.cp(np.pi / 4, 2, 3)

    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_qiskit(qubits):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.crz(np.pi / 4, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_qiskit(qubits, theta):
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.rzz(theta, *qubits)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_iswap_gate_from_qiskit():
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h([0, 1])
    qiskit_circuit.iswap(0, 1)
    cirq_circuit = from_qiskit(qiskit_circuit)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


cry = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
cry(5.518945082555831) q[2],q[1];
"""

u = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
u(5.75740842861076,5.870881397684582,1.8535618384181967) q[0];
"""

rzx = """
OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(3.4192513265994435) q1; cx q0,q1; h q1; }
qreg q[2];
rzx(3.4192513265994435) q[1],q[0];
"""

ccz = """
OPENQASM 2.0;
include "qelib1.inc";
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(-pi/4) q1; cx q0,q1; h q1; }
gate rzx(param0) q0,q1 { h q1; cx q0,q1; rz(pi/4) q1; cx q0,q1; h q1; }
gate ecr q0,q1 { rzx(pi/4) q0,q1; x q0; rzx(-pi/4) q0,q1; }
gate rzx_6320157840(param0) q0,q1 { h q1; cx q0,q1; rz(2.3200048200765524) q1; cx q0,q1; h q1; }
qreg q[3];
ecr q[2],q[0];
ccz q[0],q[2],q[1];
rzx_6320157840(2.3200048200765524) q[2],q[1];
"""

rccx = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rccx q[1],q[2],q[0];
"""

csx = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
csx q[0],q[2];
"""
