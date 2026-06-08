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
Unit tests for OpenQASM 3 conversions

"""
import braket.circuits
import numpy as np
import pytest
import qiskit
from cirq.contrib.qasm_import._lexer import QasmLexer

from qbraid.interface import circuits_allclose
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.conversions.qasm2.qasm2_to_cirq import qasm2_to_cirq
from qbraid.transpiler.conversions.qasm3.qasm3_to_cirq import qasm3_to_cirq
from qbraid.transpiler.converter import transpile

try:
    import pennylane as qml

    from qbraid.transpiler.conversions.pennylane.pennylane_to_qasm3 import pennylane_to_qasm3

    pennylane_not_installed = False
except ImportError:
    pennylane_not_installed = True


def test_one_qubit_qiskit_to_braket():
    """Test converting qiskit to braket for one qubit circuit."""
    qiskit_circuit = qiskit.QuantumCircuit(1)
    qiskit_circuit.h(0)
    qiskit_circuit.ry(np.pi / 2, 0)
    qasm3_program = transpile(qiskit_circuit, "qasm3")
    braket_circuit = transpile(qasm3_program, "braket")
    circuits_allclose(qiskit_circuit, braket_circuit, strict_gphase=True)


def test_one_qubit_braket_to_qiskit():
    """Test converting braket to qiskit for one qubit circuit."""
    braket_circuit = braket.circuits.Circuit().h(0).ry(0, np.pi / 2)
    qasm3_program = transpile(braket_circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_two_qubit_braket_to_qiskit():
    """Test converting braket to qiskit for two qubit circuit."""
    braket_circuit = braket.circuits.Circuit().h(0).cnot(0, 1)
    qasm3_program = transpile(braket_circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(braket_circuit, qiskit_circuit, strict_gphase=True)


def test_braket_to_qiskit_stdgates():
    """Test converting braket to qiskit for standard gates."""
    circuit = braket.circuits.Circuit()

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.si(1)
    circuit.t(2)
    circuit.ti(3)
    circuit.rx(0, np.pi / 4)
    circuit.ry(1, np.pi / 2)
    circuit.rz(2, 3 * np.pi / 4)
    circuit.phaseshift(3, np.pi / 8)
    circuit.v(0)
    circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    cirq_circuit = transpile(circuit, "cirq")
    qasm3_program = transpile(circuit, "qasm3")
    qasm2_program = transpile(cirq_circuit, "qasm2")
    qiskit_circuit_1 = transpile(qasm3_program, "qiskit")
    qiskit_circuit_2 = transpile(qasm2_program, "qiskit")
    assert circuits_allclose(circuit, qiskit_circuit_1, strict_gphase=False)
    assert circuits_allclose(circuit, qiskit_circuit_2, strict_gphase=False)


def test_braket_to_qiskit_vi_sxdg():
    """Test converting braket to qiskit with vi/sxdg gate with
    non-strict global phase comparison."""
    circuit = braket.circuits.Circuit().vi(0)
    qasm3_program = transpile(circuit, "qasm3")
    qiskit_circuit = transpile(qasm3_program, "qiskit")
    assert circuits_allclose(circuit, qiskit_circuit, strict_gphase=False)


def test_qasm3_to_cirq_raises_for_invalid_qasm():
    """Test that qasm3_to_cirq raises QasmError for unsupported QASM."""
    invalid_qasm = "OPENQASM 2.0;\nqreg q[1];\nbarrier q;"
    with pytest.raises(QasmError):
        qasm3_to_cirq(invalid_qasm)


def test_qasm2_to_cirq_preserves_cirq_qasm3_lexer():
    """qasm2_to_cirq must not corrupt cirq's shared QASM lexer.

    The qasm2->cirq parser previously mutated ``cirq...QasmLexer.tokens`` in
    place at import time, dropping the OpenQASM 3 tokens (e.g. ``STDGATESINC``).
    That broke cirq's built-in QASM 3 importer process-wide: a ``qasm3_to_cirq``
    call after any ``qasm2_to_cirq`` rebuilt cirq's lexer from the truncated
    token list and raised a ply ``LexError``. Assert the shared token set is
    left intact and that qasm3_to_cirq still works afterwards.
    """
    qasm2_to_cirq('OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nx q[0];\n')

    assert "STDGATESINC" in QasmLexer.tokens
    circuit = qasm3_to_cirq('OPENQASM 3.0;\ninclude "stdgates.inc";\nqubit[1] q;\nx q[0];\n')
    assert len(circuit) == 1


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_basic():
    """Test basic pennylane to QASM3 conversion with Clifford gates."""
    tape = qml.tape.QuantumScript([qml.Hadamard(0), qml.CNOT([0, 1])])
    result = pennylane_to_qasm3(tape)
    lines = result.splitlines()
    assert lines == [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        "qubit[2] q;",
        "h q[0];",
        "cx q[0], q[1];",
    ]


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_parameterized():
    """Test pennylane to QASM3 with parameterized rotation gates."""
    tape = qml.tape.QuantumScript([qml.RX(1.5707963, 0), qml.RY(3.1415926, 1), qml.RZ(0.5, 0)])
    result = pennylane_to_qasm3(tape)
    lines = result.splitlines()
    assert lines == [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        "qubit[2] q;",
        "rx(1.5707963) q[0];",
        "ry(3.1415926) q[1];",
        "rz(0.5) q[0];",
    ]


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_adjoint_gates():
    """Test pennylane to QASM3 with adjoint (dagger) gates."""
    tape = qml.tape.QuantumScript([qml.adjoint(qml.S)(0), qml.adjoint(qml.T)(1)])
    result = pennylane_to_qasm3(tape)
    lines = result.splitlines()
    assert lines == [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        "qubit[2] q;",
        "sdg q[0];",
        "tdg q[1];",
    ]


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_multiqubit():
    """Test pennylane to QASM3 with multi-qubit gates including Toffoli."""
    tape = qml.tape.QuantumScript([qml.Hadamard(0), qml.CNOT([0, 1]), qml.Toffoli([0, 1, 2])])
    result = pennylane_to_qasm3(tape)
    lines = result.splitlines()
    assert lines == [
        "OPENQASM 3.0;",
        'include "stdgates.inc";',
        "qubit[3] q;",
        "h q[0];",
        "cx q[0], q[1];",
        "ccx q[0], q[1], q[2];",
    ]


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_unsupported_gate():
    """Test pennylane to QASM3 raises ValueError for unsupported gates."""
    tape = qml.tape.QuantumScript([qml.QubitUnitary(np.eye(2), 0)])
    with pytest.raises(ValueError, match="Unsupported PennyLane gate"):
        pennylane_to_qasm3(tape)


@pytest.mark.skipif(pennylane_not_installed, reason="pennylane not installed")
def test_pennylane_to_qasm3_roundtrip():
    """Test roundtrip: pennylane tape -> QASM3 -> pennylane function."""
    tape = qml.tape.QuantumScript([qml.Hadamard(0), qml.CNOT([0, 1]), qml.RX(1.5707963, 0)])
    qasm3_str = pennylane_to_qasm3(tape)
    recovered_fn = qml.from_qasm3(qasm3_str)
    assert callable(recovered_fn)
