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

"""Unit tests for myQLM extras-based conversion functions."""

# pylint: disable=implicit-str-concat,import-outside-toplevel

import importlib.util

import pytest

from qbraid.transpiler.conversions.myqlm import (
    cirq_to_myqlm,
    myqlm_to_qiskit,
    qasm2_to_myqlm,
    qiskit_to_myqlm,
)

try:
    from qat.core import Circuit as MyQLMCircuit

    HAS_MYQLM = True
except ImportError:
    HAS_MYQLM = False

HAS_QISKIT = importlib.util.find_spec("qiskit") is not None
HAS_CIRQ = importlib.util.find_spec("cirq") is not None

pytestmark = pytest.mark.skipif(not HAS_MYQLM, reason="myqlm-interop not installed")

# ---------------------------------------------------------------------------
# Shared QASM2 fixture
# ---------------------------------------------------------------------------

BELL_QASM2 = (
    "OPENQASM 2.0;\n"
    'include "qelib1.inc";\n'
    "qreg q[2];\n"
    "creg c[2];\n"
    "h q[0];\n"
    "cx q[0], q[1];\n"
    "measure q[0] -> c[0];\n"
    "measure q[1] -> c[1];\n"
)


# ---------------------------------------------------------------------------
# qasm2_to_myqlm
# ---------------------------------------------------------------------------


class TestQasm2ToMyQLM:
    """Tests for qasm2_to_myqlm."""

    def test_returns_myqlm_circuit(self):
        """Should return a myQLM Circuit object."""
        result = qasm2_to_myqlm(BELL_QASM2)
        assert isinstance(result, MyQLMCircuit)

    def test_bell_state_contains_h_and_cnot(self):
        """Bell circuit gates should include H and CNOT."""
        result = qasm2_to_myqlm(BELL_QASM2)
        gate_names = [g[0] for g in result.iterate_simple()]
        assert "H" in gate_names
        assert "CNOT" in gate_names

    def test_single_qubit_circuit(self):
        """Single-qubit Hadamard circuit should convert without error."""
        qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nh q[0];\n'
        result = qasm2_to_myqlm(qasm)
        assert isinstance(result, MyQLMCircuit)

    def test_has_requires_extras_attribute(self):
        """Function must be marked as requiring extras."""
        assert hasattr(qasm2_to_myqlm, "requires_extras")
        assert "myqlm-interop" in qasm2_to_myqlm.requires_extras


# ---------------------------------------------------------------------------
# qiskit_to_myqlm / myqlm_to_qiskit
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_QISKIT, reason="qiskit not installed")
class TestQiskitMyQLMConversions:
    """Tests for qiskit_to_myqlm and myqlm_to_qiskit."""

    def test_qiskit_to_myqlm_returns_circuit(self):
        """qiskit_to_myqlm should return a myQLM Circuit."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        result = qiskit_to_myqlm(qc)
        assert isinstance(result, MyQLMCircuit)

    def test_myqlm_to_qiskit_returns_quantum_circuit(self):
        """myqlm_to_qiskit should return a Qiskit QuantumCircuit."""
        from qiskit import QuantumCircuit
        from qiskit.circuit import QuantumCircuit as QiskitCircuit

        qc = QuantumCircuit(2)
        qc.h(0)
        myqlm_circuit = qiskit_to_myqlm(qc)
        result = myqlm_to_qiskit(myqlm_circuit)
        assert isinstance(result, QiskitCircuit)

    def test_requires_extras_attributes_present(self):
        """Both conversion functions must have the requires_extras attribute."""
        assert hasattr(qiskit_to_myqlm, "requires_extras")
        assert hasattr(myqlm_to_qiskit, "requires_extras")


# ---------------------------------------------------------------------------
# cirq_to_myqlm
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_CIRQ, reason="cirq not installed")
class TestCirqToMyQLM:
    """Tests for cirq_to_myqlm."""

    def test_returns_myqlm_circuit(self):
        """cirq_to_myqlm should return a myQLM Circuit."""
        import cirq

        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
        result = cirq_to_myqlm(circuit)
        assert isinstance(result, MyQLMCircuit)

    def test_has_requires_extras_attribute(self):
        """Function must be marked as requiring extras."""
        assert hasattr(cirq_to_myqlm, "requires_extras")
        assert "myqlm-interop" in cirq_to_myqlm.requires_extras
