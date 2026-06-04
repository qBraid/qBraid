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
Unt tests for conversions to/from pyQuil circuits.

"""
import numpy as np
import pytest
from cirq import Circuit, LineQubit
from cirq import ops as cirq_ops
from cirq.contrib.qasm_import import circuit_from_qasm

try:
    from pyquil import Program
    from pyquil.gates import CNOT, CZ, RX, RZ, RZZ, H, I, X, Y, Z
    from pyquil.noise import _decoherence_noise_model, _get_program_gates, apply_noise_model

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.cirq import cirq_to_pyquil
    from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_pyquil
    from qbraid.transpiler.conversions.pyquil import pyquil_to_cirq
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq
    from qbraid.transpiler.exceptions import ProgramConversionError

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True

pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_to_from_pyquil():
    """Test round trip pyQuil-Cirq conversions."""
    p = Program()
    p += X(0)
    p += Y(1)
    p += Z(2)
    p += CNOT(0, 1)
    p += CZ(1, 2)
    p_cirq = pyquil_to_cirq(p)
    p_test = cirq_to_pyquil(p_cirq)
    assert p.out() == p_test.out()


def test_to_from_pyquil_parameterized():
    """Test round trip pyQuil-Cirq conversions with parameterized gates."""
    q0, q1 = (0, 1)
    p = Program()
    p += H(q0)
    p += H(q1)
    p += CNOT(q0, q1)
    p += RZ(2 * np.pi, q1)
    p += CNOT(q0, q1)
    p += H(q0)
    p += H(q1)
    p += RZ(np.pi / 4, q0)
    p += RZ(np.pi / 4, q1)
    p += H(q0)
    p += H(q1)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


QUIL_STRING = """
I 0
I 1
I 2
X 0
Y 1
Z 2
RX(pi/2) 0
RY(pi/2) 1
RZ(pi/2) 2
H 0
CZ 0 1
CNOT 1 2
CPHASE(pi/2) 0 1
CPHASE00(pi/2) 1 2
CPHASE01(pi/2) 0 1
CPHASE10(pi/2) 1 2
ISWAP 0 1
SWAP 1 2
XY(pi/2) 0 1
CCNOT 0 1 2
CSWAP 0 1 2
"""


def test_to_from_pyquil_quil_string():
    """PHASE, PSWAP, S, T, declaration, and measurement don't convert back
    and forth perfectly (in terms of labels -- the program unitaries and
    number of measurements are equivalent)."""
    p = Program(QUIL_STRING)
    p_cirq = pyquil_to_cirq(p)
    p_cirq = circuit_from_qasm(p_cirq.to_qasm())
    p_test = cirq_to_pyquil(p_cirq)
    assert circuits_allclose(p, p_test)


def test_from_pyquil_no_zero_qubit():
    """Test converting a pyQuil program with a non-zero qubit index to Cirq."""
    p = Program()
    p += X(10)
    p += Y(11)
    p += Z(12)
    p += CNOT(10, 11)
    p += CZ(11, 12)
    p_test = cirq_to_pyquil(pyquil_to_cirq(p))
    assert p.out() == p_test.out()


def test_raise_error_to_pyquil_bit_flip():
    """Test raising an error when converting a Cirq circuit with a bit flip to pyQuil."""

    with pytest.raises(ProgramConversionError):
        q0 = LineQubit(0)
        circuit = Circuit(cirq_ops.bit_flip(p=0.2).on(q0), cirq_ops.measure(q0, key="result"))
        cirq_to_pyquil(circuit)


def test_raise_error_from_pyquil_noisey():
    """Test raising an error when converting a noisey pyQuil program to Cirq."""

    with pytest.raises(ProgramConversionError):
        p = Program()
        p += RX(-np.pi / 2, 0)
        noise_model = _decoherence_noise_model(_get_program_gates(p))
        p = apply_noise_model(p, noise_model)
        pyquil_to_cirq(p)


def test_cirq_to_quil_output_rzz():
    """Test that a RZZ gate is correctly converted to Quil."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    rzz(pi) q[0], q[1];
    rzz(0) q[0], q[1];
    rzz(pi/2) q[0], q[1];
    """

    p = Program()
    p += CZ(0, 1)
    p += I(0)
    p += I(1)
    p += RZZ(np.pi / 2, 0, 1)
    cirq_circuit = qasm2_to_cirq(qasm)
    p_test: Program = cirq_to_pyquil(cirq_circuit)
    assert p_test.out().replace("pi/2", f"{np.pi/2}") == p.out()


# Benchmarking tests for openqasm3_to_pyquil
OPENQASM3_BELL_STATE = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
measure q -> c;
"""


def test_openqasm3_to_pyquil_bell_state():
    """Test conversion of Bell state circuit from OpenQASM3 to pyQuil."""
    program = openqasm3_to_pyquil(OPENQASM3_BELL_STATE)
    assert isinstance(program, Program)
    # Should have H gate and CNOT gate
    program_str = program.out()
    assert "H 0" in program_str or "H(0)" in program_str
    assert "CNOT" in program_str or "CX" in program_str


OPENQASM3_PARAMETERIZED = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
rx(1.5708) q[0];
ry(0.7854) q[1];
rz(3.1416) q[0];
"""


def test_openqasm3_to_pyquil_parameterized():
    """Test conversion of parameterized gates from OpenQASM3 to pyQuil."""
    program = openqasm3_to_pyquil(OPENQASM3_PARAMETERIZED)
    assert isinstance(program, Program)
    program_str = program.out()
    assert "RX" in program_str
    assert "RY" in program_str
    assert "RZ" in program_str


OPENQASM3_THREE_QUBIT = """
OPENQASM 3;
include "stdgates.inc";
qubit[3] q;
h q[0];
h q[1];
h q[2];
ccx q[0], q[1], q[2];
"""


def test_openqasm3_to_pyquil_three_qubit():
    """Test conversion of three-qubit Toffoli gate from OpenQASM3 to pyQuil."""
    program = openqasm3_to_pyquil(OPENQASM3_THREE_QUBIT)
    assert isinstance(program, Program)
    program_str = program.out()
    assert "CCNOT" in program_str or "TOFFOLI" in program_str


OPENQASM3_ALL_SINGLE_QUBIT = """
OPENQASM 3;
include "stdgates.inc";
qubit[1] q;
x q[0];
y q[0];
z q[0];
h q[0];
s q[0];
t q[0];
"""


def test_openqasm3_to_pyquil_all_single_qubit():
    """Test conversion of all supported single-qubit gates."""
    program = openqasm3_to_pyquil(OPENQASM3_ALL_SINGLE_QUBIT)
    assert isinstance(program, Program)
    program_str = program.out()
    assert "X" in program_str
    assert "Y" in program_str
    assert "Z" in program_str
    assert "H" in program_str
    assert "S" in program_str
    assert "T" in program_str


OPENQASM3_TWO_QUBIT = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
cx q[0], q[1];
cz q[0], q[1];
swap q[0], q[1];
"""


def test_openqasm3_to_pyquil_two_qubit():
    """Test conversion of all supported two-qubit gates."""
    program = openqasm3_to_pyquil(OPENQASM3_TWO_QUBIT)
    assert isinstance(program, Program)
    program_str = program.out()
    assert "CNOT" in program_str or "CX" in program_str
    assert "CZ" in program_str
    assert "SWAP" in program_str


def test_openqasm3_to_pyquil_unsupported_gate():
    """Test that unsupported gates raise ProgramConversionError."""
    unsupported_qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[1] q;
    phase(1.0) q[0];
    """
    with pytest.raises(ProgramConversionError, match="Unsupported gate"):
        openqasm3_to_pyquil(unsupported_qasm)
