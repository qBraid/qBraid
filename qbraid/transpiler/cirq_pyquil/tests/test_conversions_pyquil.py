# Copyright (C) 2023 qBraid
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
from pyquil import Program
from pyquil.gates import CNOT, CZ, RX, RZ, H, X, Y, Z
from pyquil.noise import _decoherence_noise_model, _get_program_gates, apply_noise_model

from qbraid.transpiler.cirq_pyquil.conversions import from_pyquil, to_pyquil
from qbraid.transpiler.exceptions import CircuitConversionError


def test_to_from_pyquil():
    p = Program()
    p += X(0)
    p += Y(1)
    p += Z(2)
    p += CNOT(0, 1)
    p += CZ(1, 2)
    p_test = to_pyquil(from_pyquil(p, compat=False), compat=False)
    assert p.out() == p_test.out()


def test_to_from_pyquil_parameterized():
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
    p_test = to_pyquil(from_pyquil(p, compat=False), compat=False)
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
    p_test = to_pyquil(from_pyquil(p, compat=False), compat=False)
    assert p.out() == p_test.out()


def test_to_pyquil_from_pyquil_no_zero_qubit():
    p = Program()
    p += X(10)
    p += Y(11)
    p += Z(12)
    p += CNOT(10, 11)
    p += CZ(11, 12)
    p_test = to_pyquil(from_pyquil(p, compat=False), compat=False)
    assert p.out() == p_test.out()


def test_raise_error_to_pyquil():
    with pytest.raises(CircuitConversionError):
        q0 = LineQubit(0)
        circuit = Circuit(cirq_ops.bit_flip(p=0.2).on(q0), cirq_ops.measure(q0, key="result"))
        to_pyquil(circuit)


def test_raise_error_from_pyquil():
    with pytest.raises(CircuitConversionError):
        p = Program()
        p += RX(-np.pi / 2, 0)
        noise_model = _decoherence_noise_model(_get_program_gates(p))
        p = apply_noise_model(p, noise_model)
        from_pyquil(p, compat=False)
