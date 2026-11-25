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
Unit tests for PennyLane to OpenQASM 2 conversion

"""
import pytest

qml = pytest.importorskip("pennylane")

# pylint: disable=wrong-import-position
from pennylane.tape import QuantumTape

from qbraid.interface import circuits_allclose
from qbraid.transpiler import Conversion, ConversionGraph, transpile
from qbraid.transpiler.conversions.pennylane import pennylane_to_qasm2


def test_pennylane_to_qasm2_numbers_qubits_by_wire_label():
    """Test that qubits are numbered by wire label, not by first use."""
    with QuantumTape() as tape:
        qml.Hadamard(1)
        qml.PauliX(0)

    assert pennylane_to_qasm2(tape).splitlines()[3:] == ["h q[1];", "x q[0];"]


def test_pennylane_to_qasm2_measures_wires_by_label():
    """Test that measurements land on the qubits of the wires they measure."""
    with QuantumTape() as tape:
        qml.Hadamard(2)
        qml.PauliX(0)
        qml.CNOT([2, 1])
        qml.probs(wires=[0, 2])

    lines = pennylane_to_qasm2(tape).splitlines()
    assert "cx q[2],q[1];" in lines
    assert lines[-2:] == ["measure q[0] -> c[0];", "measure q[2] -> c[1];"]


def test_pennylane_to_qiskit_via_qasm2_noncontiguous_wires():
    """Test that a tape on wires {0, 2} keeps its qubit order through OpenQASM 2."""
    pytest.importorskip("qiskit")
    from qbraid.transpiler.conversions.qasm2 import (  # pylint: disable=import-outside-toplevel
        qasm2_to_qiskit,
    )

    with QuantumTape() as tape:
        qml.Hadamard(2)
        qml.CNOT([2, 0])
        qml.RY(0.3, 0)

    graph = ConversionGraph(
        conversions=[
            Conversion("pennylane", "qasm2", pennylane_to_qasm2),
            Conversion("qasm2", "qiskit", qasm2_to_qiskit),
        ]
    )
    circuit = transpile(tape, "qiskit", conversion_graph=graph)
    assert circuits_allclose(tape, circuit, index_contig=True)
