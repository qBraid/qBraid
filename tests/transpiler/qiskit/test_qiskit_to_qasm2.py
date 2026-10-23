# Copyright 2026 qBraid
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

"""Strict OpenQASM 2 export and circuit semantics."""

import pytest
from qiskit import QuantumCircuit, qasm2
from qiskit.circuit.library import PhaseGate, SdgGate, SGate, TGate
from qiskit.quantum_info import Operator

from qbraid.transpiler import transpile
from qbraid.transpiler.conversions.qasm3 import qasm3_to_qiskit
from qbraid.transpiler.conversions.qiskit import qiskit_to_qasm2


@pytest.mark.parametrize("gate", [SGate(), SdgGate(), TGate(), PhaseGate(0.37)])
def test_controlled_phase_exports_standard_qasm2(gate):
    """Controlled phase definitions must not depend on Qiskit's extended qelib1."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.h(1)
    circuit.append(gate.control(), [0, 1])
    original = circuit.copy()

    restored = qasm2.loads(qiskit_to_qasm2(circuit), strict=True)

    assert Operator(restored).equiv(Operator(original))
    assert circuit == original


@pytest.mark.parametrize("name", ["s", "sdg", "t"])
def test_qasm3_controlled_phase_fallback_exports_standard_qasm2(name):
    """A modifier unsupported by the Cirq edge must still yield parseable QASM 2."""
    source = f"""OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
h q[1];
ctrl @ {name} q[0], q[1];
"""
    restored = qasm2.loads(transpile(source, "qasm2"), strict=True)

    assert Operator(restored).equiv(Operator(qasm3_to_qiskit(source)))


def test_nested_custom_gate_exports_standard_qasm2():
    """Nonstandard phase gates inside a custom definition need lowering too."""
    inner = QuantumCircuit(2, name="inner")
    inner.cp(0.37, 0, 1)
    outer = QuantumCircuit(2, name="outer")
    outer.append(inner.to_gate(), [1, 0])
    circuit = QuantumCircuit(2)
    circuit.append(outer.to_gate(), [0, 1])

    restored = qasm2.loads(qiskit_to_qasm2(circuit), strict=True)

    assert Operator(restored).equiv(Operator(circuit))


def test_qasm2_export_preserves_measurement_registers_and_bit_order():
    """Lowering a controlled phase must preserve crossed measurement assignments."""
    circuit = QuantumCircuit(3, 3)
    circuit.x(2)
    circuit.cp(0.37, 0, 1)
    circuit.measure([2, 0, 1], [0, 1, 2])
    original = circuit.copy()

    restored = qasm2.loads(qiskit_to_qasm2(circuit), strict=True)
    assignments = [
        (restored.find_bit(op.qubits[0]).index, restored.find_bit(op.clbits[0]).index)
        for op in restored.data
        if op.operation.name == "measure"
    ]

    assert restored.qregs == circuit.qregs
    assert restored.cregs == circuit.cregs
    assert assignments == [(2, 0), (0, 1), (1, 2)]
    assert circuit == original


def test_standard_export_preserves_custom_gate_phase():
    """Keep valid definitions whose exact phase would be lost by basis translation."""
    root_x = QuantumCircuit(1, name="root_x")
    root_x.h(0)
    root_x.s(0)
    root_x.h(0)
    circuit = QuantumCircuit(2)
    circuit.append(root_x.to_gate(), [0])
    circuit.iswap(0, 1)
    original = circuit.copy()

    exported = qiskit_to_qasm2(circuit)
    restored = qasm2.loads(exported, strict=True)

    assert exported == qasm2.dumps(original)
    assert Operator(restored) == Operator(original)
    assert circuit == original
