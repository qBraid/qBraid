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

"""Unit tests for qibo <-> qasm3 conversion functions."""

# pylint: disable=implicit-str-concat

import math

import pytest

from qbraid.transpiler.conversions.qibo import qasm3_to_qibo, qibo_to_qasm3
from qbraid.transpiler.exceptions import ProgramConversionError

try:
    import qibo
    import qibo.gates
    import qibo.models

    HAS_QIBO = True
except ImportError:
    HAS_QIBO = False

pytestmark = pytest.mark.skipif(not HAS_QIBO, reason="qibo is not installed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bell() -> "qibo.models.Circuit":
    """Return a 2-qubit Bell-state circuit (H + CNOT)."""
    c = qibo.models.Circuit(2)
    c.add(qibo.gates.H(0))
    c.add(qibo.gates.CNOT(0, 1))
    return c


def _single_qubit() -> "qibo.models.Circuit":
    """Return a 1-qubit circuit with H, S, T gates."""
    c = qibo.models.Circuit(1)
    c.add(qibo.gates.H(0))
    c.add(qibo.gates.S(0))
    c.add(qibo.gates.T(0))
    return c


# ---------------------------------------------------------------------------
# qibo_to_qasm3
# ---------------------------------------------------------------------------


class TestQiboToQasm3:
    """Tests for the qibo_to_qasm3 conversion function."""

    def test_header_present(self):
        """Emitted string should contain a valid QASM 3 header."""
        result = qibo_to_qasm3(_bell())
        assert "OPENQASM 3.0;" in result
        assert 'include "stdgates.inc";' in result

    def test_qubit_register(self):
        """Qubit register declaration should match the circuit width."""
        result = qibo_to_qasm3(_bell())
        assert "qubit[2] q;" in result

    def test_bell_gates(self):
        """Bell circuit should produce h and cx gate statements."""
        result = qibo_to_qasm3(_bell())
        assert "h q[0];" in result
        assert "cx q[0], q[1];" in result

    def test_single_qubit_gates(self):
        """H, S, and T gates should map to their QASM 3 equivalents."""
        result = qibo_to_qasm3(_single_qubit())
        assert "h q[0];" in result
        assert "s q[0];" in result
        assert "t q[0];" in result

    def test_measurement_classical_register(self):
        """Circuits with measurements should include a bit register."""
        c = qibo.models.Circuit(2)
        c.add(qibo.gates.H(0))
        c.add(qibo.gates.M(0, 1))
        result = qibo_to_qasm3(c)
        assert "bit[2] c;" in result
        assert "measure q[0] -> c[0];" in result
        assert "measure q[1] -> c[1];" in result

    def test_no_measurements_omits_classical_register(self):
        """Circuits without measurements should not declare a bit register."""
        result = qibo_to_qasm3(_bell())
        assert not any(line.strip().startswith("bit[") for line in result.splitlines())

    def test_parametric_rx(self):
        """RX gate should be emitted with its angle parameter."""
        c = qibo.models.Circuit(1)
        c.add(qibo.gates.RX(0, theta=math.pi / 2))
        result = qibo_to_qasm3(c)
        assert "rx(" in result
        assert "q[0]" in result

    def test_cz_gate(self):
        """CZ gate should map to cz in QASM 3."""
        c = qibo.models.Circuit(2)
        c.add(qibo.gates.CZ(0, 1))
        result = qibo_to_qasm3(c)
        assert "cz q[0], q[1];" in result

    def test_swap_gate(self):
        """SWAP gate should map to swap in QASM 3."""
        c = qibo.models.Circuit(2)
        c.add(qibo.gates.SWAP(0, 1))
        result = qibo_to_qasm3(c)
        assert "swap q[0], q[1];" in result

    def test_toffoli_gate(self):
        """TOFFOLI gate should map to ccx in QASM 3."""
        c = qibo.models.Circuit(3)
        c.add(qibo.gates.TOFFOLI(0, 1, 2))
        result = qibo_to_qasm3(c)
        assert "ccx q[0], q[1], q[2];" in result

    @pytest.mark.parametrize(
        "gate_name, qasm_name",
        [("Z", "z"), ("Y", "y"), ("X", "x"), ("T", "t"), ("S", "s")],
    )
    def test_common_single_qubit_gates(self, gate_name, qasm_name):
        """Common single-qubit gates should map to their QASM 3 lowercase names."""
        c = qibo.models.Circuit(1)
        c.add(getattr(qibo.gates, gate_name)(0))
        result = qibo_to_qasm3(c)
        assert f"{qasm_name} q[0];" in result

    def test_unsupported_gate_raises(self):
        """An unrecognised gate class should raise ProgramConversionError."""

        class _FakeGate(qibo.gates.H):
            """Subclass with an unrecognised name — triggers ProgramConversionError."""

        c = qibo.models.Circuit(1)
        c.queue.append(_FakeGate(0))
        with pytest.raises(ProgramConversionError):
            qibo_to_qasm3(c)


# ---------------------------------------------------------------------------
# qasm3_to_qibo
# ---------------------------------------------------------------------------


class TestQasm3ToQibo:
    """Tests for the qasm3_to_qibo conversion function."""

    def test_bell_nqubits(self):
        """Bell-state QASM 3 string should produce a 2-qubit circuit."""
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[2] q;\n"
            "h q[0];\n"
            "cx q[0], q[1];\n"
        )
        assert qasm3_to_qibo(qasm).nqubits == 2

    def test_bell_gate_count(self):
        """Bell-state QASM 3 string should yield exactly two gates."""
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[2] q;\n"
            "h q[0];\n"
            "cx q[0], q[1];\n"
        )
        assert len(qasm3_to_qibo(qasm).queue) == 2

    def test_measurement_parsed(self):
        """Measurement statements should be added to the circuit queue."""
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[1] q;\n"
            "bit[1] c;\n"
            "h q[0];\n"
            "measure q[0] -> c[0];\n"
        )
        circuit = qasm3_to_qibo(qasm)
        assert circuit.nqubits == 1
        assert len(circuit.queue) == 2

    def test_parametric_rx_value(self):
        """Parsed RX gate should carry the correct angle."""
        angle = math.pi / 2
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[1] q;\n"
            f"rx({angle:.10g}) q[0];\n"
        )
        circuit = qasm3_to_qibo(qasm)
        assert len(circuit.queue) == 1
        assert abs(circuit.queue[0].parameters[0] - angle) < 1e-8

    def test_pi_expression_in_parameter(self):
        """The literal 'pi' in a parameter expression should evaluate correctly."""
        qasm = "OPENQASM 3.0;\n" 'include "stdgates.inc";\n' "qubit[1] q;\n" "rx(pi/2) q[0];\n"
        circuit = qasm3_to_qibo(qasm)
        assert abs(circuit.queue[0].parameters[0] - math.pi / 2) < 1e-8

    def test_three_qubit_ccx(self):
        """ccx instruction should produce a 3-qubit circuit with one gate."""
        qasm = (
            "OPENQASM 3.0;\n" 'include "stdgates.inc";\n' "qubit[3] q;\n" "ccx q[0], q[1], q[2];\n"
        )
        circuit = qasm3_to_qibo(qasm)
        assert circuit.nqubits == 3
        assert len(circuit.queue) == 1

    def test_missing_qubit_declaration_raises(self):
        """Strings without a qubit register declaration should raise ProgramConversionError."""
        with pytest.raises(ProgramConversionError, match="qubit count"):
            qasm3_to_qibo("OPENQASM 3.0;\nh q[0];\n")

    def test_unsupported_gate_raises(self):
        """An unknown gate name should raise ProgramConversionError."""
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[1] q;\n"
            "nonexistent_gate_xyz q[0];\n"
        )
        with pytest.raises(ProgramConversionError):
            qasm3_to_qibo(qasm)

    def test_comment_lines_ignored(self):
        """Comment lines should be silently skipped."""
        qasm = (
            "OPENQASM 3.0;\n"
            'include "stdgates.inc";\n'
            "qubit[1] q;\n"
            "// This is a comment\n"
            "h q[0];\n"
        )
        assert len(qasm3_to_qibo(qasm).queue) == 1


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    """End-to-end round-trip tests: qibo -> qasm3 -> qibo."""

    def test_bell_roundtrip_nqubits(self):
        """Round-tripped Bell circuit should have the same qubit count."""
        original = _bell()
        assert qasm3_to_qibo(qibo_to_qasm3(original)).nqubits == original.nqubits

    def test_bell_roundtrip_gate_count(self):
        """Round-tripped Bell circuit should have the same number of gates."""
        original = _bell()
        reconstructed = qasm3_to_qibo(qibo_to_qasm3(original))
        assert len(reconstructed.queue) == len(original.queue)

    def test_single_qubit_roundtrip(self):
        """Round-tripped single-qubit circuit should preserve gate count."""
        original = _single_qubit()
        reconstructed = qasm3_to_qibo(qibo_to_qasm3(original))
        assert reconstructed.nqubits == 1
        assert len(reconstructed.queue) == len(original.queue)

    def test_parametric_roundtrip_angle(self):
        """RX angle should survive a qibo -> qasm3 -> qibo round-trip."""
        angle = math.pi / 3
        c = qibo.models.Circuit(1)
        c.add(qibo.gates.RX(0, theta=angle))
        reconstructed = qasm3_to_qibo(qibo_to_qasm3(c))
        assert abs(reconstructed.queue[0].parameters[0] - angle) < 1e-6
