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

from qbraid.programs.testing.circuit_equality import circuits_allclose
from qbraid.programs.testing.random import random_circuit

from .._data.programs import bell_data, shared15_data

bell_map, _ = bell_data()
braket_bell = bell_map["braket"]()
cirq_bell = bell_map["cirq"]()
pyquil_bell = bell_map["pyquil"]()
qiskit_bell = bell_map["qiskit"]()
pytket_bell = bell_map["pytket"]()
qasm2_bell = bell_map["qasm2"]()
qasm3_bell = bell_map["qasm3"]()

shared15_map, _ = shared15_data()
braket_shared15 = shared15_map["braket"]()
cirq_shared15 = shared15_map["cirq"]()
pyquil_shared15 = shared15_map["pyquil"]()
qiskit_shared15 = shared15_map["qiskit"]()
pytket_shared15 = shared15_map["pytket"]()
qasm2_shared15 = shared15_map["qasm2"]()
qasm3_shared15 = shared15_map["qasm3"]()


def test_bell():
    """Test the equality of bell circuits"""

    eq1 = circuits_allclose(braket_bell, cirq_bell, strict_gphase=True)
    eq2 = circuits_allclose(cirq_bell, pyquil_bell, strict_gphase=True)
    eq3 = circuits_allclose(pyquil_bell, qiskit_bell, strict_gphase=True)
    eq4 = circuits_allclose(qiskit_bell, pytket_bell, strict_gphase=True)
    eq5 = circuits_allclose(pytket_bell, qasm2_bell, strict_gphase=True)
    eq6 = circuits_allclose(qasm2_bell, qasm3_bell, strict_gphase=True)

    assert eq1 and eq2 and eq3 and eq4 and eq5 and eq6


def test_shared15():
    """Test the equality of shared gates circuits"""

    eq1 = circuits_allclose(braket_shared15, cirq_shared15, strict_gphase=True)
    eq2 = circuits_allclose(cirq_shared15, pyquil_shared15, strict_gphase=False)
    eq3 = circuits_allclose(pyquil_shared15, qiskit_shared15, strict_gphase=False)
    eq4 = circuits_allclose(qiskit_shared15, pytket_shared15, strict_gphase=True)
    eq5 = circuits_allclose(pytket_shared15, qasm2_shared15, strict_gphase=True)
    eq6 = circuits_allclose(qasm2_shared15, qasm3_shared15, strict_gphase=False)

    assert eq1 and eq2 and eq3 and eq4 and eq5 and eq6


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    try:
        random_circuit(package)
    except Exception:  # pylint: disable=broad-exception-caught
        assert False
    assert True
