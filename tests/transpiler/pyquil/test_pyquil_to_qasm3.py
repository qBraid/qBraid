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
Unit tests for pyQuil to OpenQASM 3 conversion.

"""

import pytest

# Imported at top (not inside the pyquil guard) so a regression in the converter
# surfaces as a test failure rather than being masked as "pyquil not installed".
from qbraid.transpiler.conversions.pyquil.pyquil_to_qasm3 import pyquil_to_qasm3
from qbraid.transpiler.exceptions import ProgramConversionError

try:
    from pyquil import Program
    from pyquil.gates import (
        CNOT,
        CPHASE,
        CPHASE00,
        ISWAP,
        MEASURE,
        PSWAP,
        RESET,
        RX,
        RZ,
        RZZ,
        SQISW,
        H,
        S,
        T,
        U,
    )
    from pyquil.quilatom import QubitPlaceholder
    from pyquil.quilbase import DelayQubits, Fence

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")

_HEADER = 'OPENQASM 3.0;\ninclude "stdgates.inc";\n'


def test_pyquil_to_qasm3_bell():
    """Bell circuit converts to the expected OpenQASM 3 program."""
    result = pyquil_to_qasm3(Program(H(0), CNOT(0, 1)))
    expected = _HEADER + "qubit[2] q;\nh q[0];\ncx q[0], q[1];\n"
    assert result == expected


def test_pyquil_to_qasm3_parameterized():
    """Parameterized gates map to rx/rz/cp with their angles."""
    result = pyquil_to_qasm3(Program(RX(0.5, 0), RZ(1.2, 1), CPHASE(0.3, 0, 1)))
    expected = _HEADER + "qubit[2] q;\nrx(0.5) q[0];\nrz(1.2) q[1];\ncp(0.3) q[0], q[1];\n"
    assert result == expected


def test_pyquil_to_qasm3_u_gate():
    """pyQuil's U(theta, phi, lambda) maps to the OpenQASM 3 u gate."""
    result = pyquil_to_qasm3(Program(U(0.1, 0.2, 0.3, 0)))
    expected = _HEADER + "qubit[1] q;\nu(0.1, 0.2, 0.3) q[0];\n"
    assert result == expected


def test_pyquil_to_qasm3_dagger():
    """S/T daggers map to sdg/tdg."""
    result = pyquil_to_qasm3(Program(S(0).dagger(), T(1).dagger()))
    expected = _HEADER + "qubit[2] q;\nsdg q[0];\ntdg q[1];\n"
    assert result == expected


def test_pyquil_to_qasm3_measurement():
    """Measurement produces a bit register declaration and measure assignments."""
    program = Program()
    ro = program.declare("ro", "BIT", 2)
    program += H(0)
    program += CNOT(0, 1)
    program += MEASURE(0, ro[0])
    program += MEASURE(1, ro[1])

    result = pyquil_to_qasm3(program)
    expected = _HEADER + (
        "qubit[2] q;\n"
        "bit[2] ro;\n"
        "h q[0];\n"
        "cx q[0], q[1];\n"
        "ro[0] = measure q[0];\n"
        "ro[1] = measure q[1];\n"
    )
    assert result == expected


def test_pyquil_to_qasm3_qubit_register_spans_highest_index():
    """A gap in used qubit indices still yields a register sized to the max index."""
    result = pyquil_to_qasm3(Program(H(0), CNOT(0, 2)))
    expected = _HEADER + "qubit[3] q;\nh q[0];\ncx q[0], q[2];\n"
    assert result == expected


def test_pyquil_to_qasm3_extended_gates():
    """Gates recognized by pyqasm beyond the official stdgates set are mapped."""
    result = pyquil_to_qasm3(
        Program(ISWAP(0, 1), RZZ(0.5, 0, 1), PSWAP(0.3, 0, 1), CPHASE00(0.2, 0, 1))
    )
    expected = _HEADER + (
        "qubit[2] q;\n"
        "iswap q[0], q[1];\n"
        "rzz(0.5) q[0], q[1];\n"
        "pswap(0.3) q[0], q[1];\n"
        "cphaseshift00(0.2) q[0], q[1];\n"
    )
    assert result == expected


def test_pyquil_to_qasm3_reset():
    """RESET maps to an OpenQASM 3 reset on the target qubit."""
    result = pyquil_to_qasm3(Program(H(0), RESET(0)))
    expected = _HEADER + "qubit[1] q;\nh q[0];\nreset q[0];\n"
    assert result == expected


def test_pyquil_to_qasm3_barrier():
    """FENCE maps to an OpenQASM 3 barrier over its qubits."""
    program = Program(H(0))
    program += Fence([0, 1])
    result = pyquil_to_qasm3(program)
    expected = _HEADER + "qubit[2] q;\nh q[0];\nbarrier q[0], q[1];\n"
    assert result == expected


def test_pyquil_to_qasm3_delay():
    """DELAY maps to an OpenQASM 3 delay with the duration in seconds."""
    program = Program(H(0))
    program += DelayQubits([0], 1e-7)
    out = pyquil_to_qasm3(program)
    assert "delay[1e-07s] q[0];" in out


def test_pyquil_to_qasm3_unsupported_gate_raises():
    """A gate with no pyqasm equivalent (e.g. SQISW) raises ProgramConversionError."""
    with pytest.raises(ProgramConversionError):
        pyquil_to_qasm3(Program(SQISW(0, 1)))


def test_pyquil_to_qasm3_placeholder_qubit_raises():
    """A non-fixed qubit (QubitPlaceholder) raises a clean ProgramConversionError."""
    with pytest.raises(ProgramConversionError):
        pyquil_to_qasm3(Program(H(QubitPlaceholder())))


def test_pyquil_to_qasm3_feedforward_unsupported_raises():
    """Classical feed-forward (JUMP-WHEN) is a documented limitation and raises."""
    program = Program()
    ro = program.declare("ro", "BIT", 1)
    program += MEASURE(0, ro[0])
    program.if_then(ro[0], Program(H(1)))
    with pytest.raises(ProgramConversionError):
        pyquil_to_qasm3(program)
