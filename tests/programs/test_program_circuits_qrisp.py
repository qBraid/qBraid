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
Unit tests for qbraid.programs.qrisp.QrispCircuit

"""

import pytest

from qbraid.programs.exceptions import ProgramTypeError

try:
    from qrisp import QuantumCircuit

    from qbraid.programs.gate_model.qrisp import QrispCircuit

    qrisp_not_installed = False
except ImportError:
    qrisp_not_installed = True

pytestmark = pytest.mark.skipif(qrisp_not_installed, reason="qrisp not installed")


def test_reverse_qubit_order():
    """Test reversing ordering of qubits in qrisp circuit"""
    circ = QuantumCircuit(3)
    circ.h(0)
    circ.cx(0, 2)

    qprogram = QrispCircuit(circ)
    qprogram.reverse_qubit_order()
    reversed_circ = qprogram.program

    expected_circ = QuantumCircuit(3)
    expected_circ.h(2)
    expected_circ.cx(2, 0)

    # Since qubit names will differ we need to compare via cirq
    assert reversed_circ.to_cirq() == expected_circ.to_cirq(), (
        "The reversed circuit does not match the expected output."
    )


def test_remove_idle_qubits_qrisp():
    """Test convert_to_contigious on qrisp circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QrispCircuit(circuit)
    qprogram.remove_idle_qubits()
    assert qprogram.num_qubits == 2

    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 2)
    qprogram = QrispCircuit(circuit)
    qprogram.remove_idle_qubits()
    assert qprogram.num_qubits == 2


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        QrispCircuit("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_circuit_properties():
    """Test properties of QrispCircuit"""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QrispCircuit(circuit)
    assert len(qprogram.qubits) == 2
    assert qprogram.num_qubits == 2
    assert qprogram.num_clbits == 0
    assert qprogram.depth == 2
