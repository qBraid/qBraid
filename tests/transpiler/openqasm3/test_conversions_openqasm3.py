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
Unit tests for OpenQASM 3 to pyQuil conversion.

"""

import math

import pytest

try:
    from pyquil import Program
    from pyquil.gates import CNOT, CPHASE, RX, RZ, H, I, S, T, U, X

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.openqasm3.openqasm3_to_pyquil import openqasm3_to_pyquil
    from qbraid.transpiler.exceptions import ProgramConversionError

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_openqasm3_to_pyquil_bell():
    """Bell circuit converts and matches an explicit pyQuil reference."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    cx q[0], q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    expected = Program(H(0), CNOT(0, 1))
    assert circuits_allclose(result, expected, strict_gphase=False)


def test_openqasm3_to_pyquil_parameterized():
    """Parameterized gates convert and match an explicit pyQuil reference."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    rx(0.5) q[0];
    rz(1.2) q[1];
    cp(0.3) q[0], q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    expected = Program(RX(0.5, 0), RZ(1.2, 1), CPHASE(0.3, 0, 1))
    assert circuits_allclose(result, expected, strict_gphase=False)


def test_openqasm3_to_pyquil_measurement():
    """Measurement produces a DECLARE + MEASURE."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] c;
    h q[0];
    cx q[0], q[1];
    c[0] = measure q[0];
    c[1] = measure q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    out = result.out()
    assert "DECLARE ro BIT[2]" in out
    assert out.count("MEASURE") == 2


def test_openqasm3_to_pyquil_barrier_fence():
    """Barrier maps to a pyQuil FENCE over its qubits, preserving surrounding gates."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    h q[0];
    barrier q;
    cx q[0], q[1];
    """
    out = openqasm3_to_pyquil(qasm).out()
    assert "H 0" in out
    assert "FENCE 0 1" in out
    assert "CNOT 0 1" in out


def test_openqasm3_to_pyquil_idle_qubits_padded():
    """Declared-but-unused qubits are padded with I so the register width is preserved."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[4] q;
    x q[0];
    x q[2];
    x q[3];
    """
    result = openqasm3_to_pyquil(qasm)
    # q[1] is idle; without padding the program would be 3-qubit and mismatch the
    # 4-qubit reference operator.
    expected = Program(X(0), X(2), X(3), I(1))
    assert circuits_allclose(result, expected, strict_gphase=False)


def test_openqasm3_to_pyquil_reset():
    """reset maps to pyQuil RESET on the target qubit."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    x q[0];
    reset q[0];
    """
    out = openqasm3_to_pyquil(qasm).out()
    assert "X 0" in out
    assert "RESET 0" in out


def test_openqasm3_to_pyquil_delay():
    """delay maps to pyQuil DELAY with the duration converted to seconds."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[1] q;
    delay[100ns] q[0];
    """
    out = openqasm3_to_pyquil(qasm).out()
    assert "DELAY 0" in out


def test_openqasm3_to_pyquil_feedforward():
    """if (c == 1) classical feedforward maps to a conditional JUMP-WHEN block."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[1] c;
    h q[0];
    c[0] = measure q[0];
    if (c[0] == 1) {
        x q[1];
    }
    """
    result = openqasm3_to_pyquil(qasm)
    result.resolve_label_placeholders()
    out = result.out()
    assert "MEASURE 0 ro[0]" in out
    assert "JUMP-WHEN" in out
    assert "X 1" in out


def test_openqasm3_to_pyquil_feedforward_else():
    """if/else feedforward emits both branches conditioned on the measured bit."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[1] c;
    c[0] = measure q[0];
    if (c[0] == 1) {
        x q[1];
    } else {
        z q[1];
    }
    """
    result = openqasm3_to_pyquil(qasm)
    result.resolve_label_placeholders()
    out = result.out()
    assert "JUMP-WHEN" in out
    assert "X 1" in out
    assert "Z 1" in out


def test_openqasm3_to_pyquil_feedforward_eq0_no_else():
    """if (c == 0) without an else must not crash (the swap path) and still emit the body."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[1] c;
    c[0] = measure q[0];
    if (c[0] == 0) {
        x q[1];
    }
    """
    result = openqasm3_to_pyquil(qasm)
    result.resolve_label_placeholders()
    out = result.out()
    assert "JUMP-WHEN" in out
    assert "X 1" in out


def test_openqasm3_to_pyquil_special_gates():
    """Gates needing bespoke handling (sx/sxdg -> RX(+-pi/2), u/u3 -> U, tdg -> T-dagger)."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[1] q;
    sx q[0];
    sxdg q[0];
    tdg q[0];
    u(0.1, 0.2, 0.3) q[0];
    """
    result = openqasm3_to_pyquil(qasm)
    expected = Program(
        RX(math.pi / 2, 0),
        RX(-math.pi / 2, 0),
        T(0).dagger(),
        U(0.1, 0.2, 0.3, 0),
    )
    assert circuits_allclose(result, expected, strict_gphase=False)


def test_openqasm3_to_pyquil_gate_modifiers():
    """Gate modifiers (inv/ctrl/pow/negctrl) are decomposed by pyqasm and convert correctly."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    inv @ s q[0];
    ctrl @ x q[0], q[1];
    pow(2) @ x q[0];
    negctrl @ x q[0], q[1];
    """
    result = openqasm3_to_pyquil(qasm)
    # inv @ s -> S-dagger; ctrl @ x -> CNOT; pow(2) @ x -> X X; negctrl @ x -> X CNOT X
    expected = Program(S(0).dagger(), CNOT(0, 1), X(0), X(0), X(0), CNOT(0, 1), X(0))
    assert circuits_allclose(result, expected, strict_gphase=False)


def test_openqasm3_to_pyquil_malformed_raises():
    """Malformed QASM raises ProgramConversionError."""
    with pytest.raises(ProgramConversionError):
        openqasm3_to_pyquil("OPENQASM 3.0; this is not valid;")


def test_openqasm3_to_pyquil_unsupported_condition_raises():
    """A branch condition the converter cannot express raises ProgramConversionError."""
    qasm = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] c;
    c[0] = measure q[0];
    c[1] = measure q[1];
    if (c[0] == 1 && c[1] == 1) {
        x q[0];
    }
    """
    with pytest.raises(ProgramConversionError):
        openqasm3_to_pyquil(qasm)
