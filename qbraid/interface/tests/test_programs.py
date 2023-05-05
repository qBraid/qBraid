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
Unit tests for equivalence of interfacing quantum programs

"""
import pytest

from qbraid.interface.calculate_unitary import circuits_allclose
from qbraid.interface.draw_circuit import ProgramTypeError, draw
from qbraid.interface.programs import bell_data, random_circuit, shared15_data


def test_bell():
    """Test the equality of bell circuits"""
    map, _ = bell_data()
    braket_bell = map["braket"]()
    cirq_bell = map["cirq"]()
    pyquil_bell = map["pyquil"]()
    qiskit_bell = map["qiskit"]()
    pytket_bell = map["pytket"]()

    eq1 = circuits_allclose(braket_bell, cirq_bell, strict_gphase=True)
    eq2 = circuits_allclose(cirq_bell, pyquil_bell, strict_gphase=True)
    eq3 = circuits_allclose(pyquil_bell, qiskit_bell, strict_gphase=True)
    eq4 = circuits_allclose(qiskit_bell, pytket_bell, strict_gphase=True)

    assert eq1 and eq2 and eq3 and eq4


def test_shared15():
    """Test the equality of shared gates circuits"""
    map, _ = shared15_data()
    braket_shared15 = map["braket"]()
    cirq_shared15 = map["cirq"]()
    qiskit_shared15 = map["qiskit"]()
    pytket_shared15 = map["pytket"]()

    eq1 = circuits_allclose(braket_shared15, cirq_shared15, strict_gphase=True)
    eq2 = circuits_allclose(cirq_shared15, qiskit_shared15, strict_gphase=True)
    eq3 = circuits_allclose(qiskit_shared15, pytket_shared15, strict_gphase=True)

    assert eq1 and eq2 and eq3


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    try:
        random_circuit(package)
    except Exception:
        assert False
    assert True


@pytest.mark.parametrize("draw_data", [("braket", 67), ("cirq", 42), ("qiskit", 80)])
def test_draw(capfd, draw_data):
    """Test that draw function standard output is of the expected length."""
    package, num_out = draw_data
    map, _ = bell_data()
    program = map[package]()
    draw(program)
    out, err = capfd.readouterr()
    assert len(err) == 0
    assert len(out) == num_out


def test_draw_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        draw("bad_input")
