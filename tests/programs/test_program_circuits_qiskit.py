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
Unit tests for qbraid.programs.qiskit.QiskitCircuit

"""
import pytest
from qiskit import QuantumCircuit

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.qiskit import QiskitCircuit


def test_reverse_qubit_order():
    """Test reversing ordering of qubits in qiskit circuit"""
    circ = QuantumCircuit(3)
    circ.h(0)
    circ.cx(0, 2)

    qprogram = QiskitCircuit(circ)
    qprogram.reverse_qubit_order()
    reversed_circ = qprogram.program

    expected_circ = QuantumCircuit(3)
    expected_circ.h(2)
    expected_circ.cx(2, 0)

    assert (
        reversed_circ == expected_circ
    ), "The reversed circuit does not match the expected output."


def test_remove_idle_qubits_qiskit():
    """Test convert_to_contigious on qiskit circuit"""
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QiskitCircuit(circuit)
    qprogram.remove_idle_qubits()
    contig_circuit = qprogram.program
    assert contig_circuit.num_qubits == 2


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        QiskitCircuit("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_circuit_properties():
    """Test properties of QiskitCircuit"""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    qprogram = QiskitCircuit(circuit)
    assert len(qprogram.qubits) == 2
    assert qprogram.num_qubits == 2
    assert qprogram.num_clbits == 0
    assert qprogram.depth == 2
