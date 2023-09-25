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

from qbraid import circuit_wrapper
from qbraid.exceptions import ProgramTypeError, VisualizationError
from qbraid.interface.circuit_drawer import circuit_drawer
from qbraid.interface.circuit_equality import circuits_allclose
from qbraid.interface.random_circuit import random_circuit

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


def test_draw_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer("bad_input")


def test_draw_program_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer(None)


def test_qiskit_draw():
    """Test draw function standard output for qiskit bell circuit."""
    expected = """          ┌───┐
q_0: ─────┤ X ├
     ┌───┐└─┬─┘
q_1: ┤ H ├──■──
     └───┘     """
    qprogram = circuit_wrapper(qiskit_bell)
    qprogram.reverse_qubit_order()
    result = circuit_drawer(qprogram.program, output="text")
    assert str(result) == expected


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"])
def test_braket_bell_draw(capfd, package):
    """Test using Amazon Braket to draw using ascii output is of the expected length."""
    # pylint: disable=eval-used
    circuit_wrapper(eval(f"{package}_bell")).draw(package="braket", output="ascii")

    out, err = capfd.readouterr()
    assert len(err) == 0
    assert len(out) == 67


# todo: shared15 draw testcase, after fixing circuit decomposition problem from cirq


def test_braket_raises():
    """Test that drawing braket circuit with non-supported output raises error"""
    with pytest.raises(VisualizationError):
        circuit_drawer(braket_bell, output="bad_input")


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"])
def test_cirq_bell_text_draw(capfd, package):
    """Test using Cirq to draw circuit using text output is of the expected length."""
    # pylint: disable=eval-used
    circuit_wrapper(eval(f"{package}_bell")).draw(package="cirq", output="text")

    out, err = capfd.readouterr()
    assert len(err) == 0
    if package in ["pytket", "qasm2"]:  # todo: there is "q_n" represent number of qubit
        assert len(out) == 48
    else:
        assert len(out) == 42


def test_cirq_bell_svg_draw():
    """Test drawing Cirq circuit using SVG source output"""
    svg_str = circuit_drawer(cirq_bell, output="svg_source")
    assert svg_str.startswith("<svg") and svg_str.endswith("</svg>")


def test_cirq_raises():
    """Test that drawing Cirq circuit with non-supported output raises error"""
    with pytest.raises(VisualizationError):
        circuit_drawer(cirq_bell, output="bad_input")


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"])
def test_pyquil_bell_draw(capfd, package):
    """Test using pyquil to draw circuit using text output is of the expected length."""
    # pylint: disable=eval-used
    circuit_wrapper(eval(f"{package}_bell")).draw(package="pyquil", output="text")

    out, err = capfd.readouterr()
    assert len(err) == 0
    assert len(out) == 14


def test_pyquil_raises():
    """Test that drawing pyQuil program with non-supported output raises error"""
    with pytest.raises(VisualizationError):
        circuit_drawer(pyquil_bell, output="bad_input")


def test_pytket_draw():
    """Test draw function html output for pytket bell circuit."""
    assert len(circuit_drawer(pytket_bell, output="html")) == 2381


def test_pytket_raises():
    """Test that drawing pytket circuit with non-supported output raises error"""
    with pytest.raises(VisualizationError):
        circuit_drawer(pytket_bell, output="bad_input")
