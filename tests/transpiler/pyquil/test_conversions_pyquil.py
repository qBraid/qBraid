# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
