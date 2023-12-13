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
Unit tests for circuit drawer

# TODO: shared15 draw testcase, after fixing circuit decomposition problem from cirq

"""
import pytest

from qbraid import circuit_wrapper
from qbraid.exceptions import ProgramTypeError, VisualizationError
from qbraid.visualization.draw_circuit import circuit_drawer

from ..fixtures.programs import bell_data

bell_map, _ = bell_data()
braket_bell = bell_map["braket"]()
cirq_bell = bell_map["cirq"]()
pyquil_bell = bell_map["pyquil"]()
qiskit_bell = bell_map["qiskit"]()
pytket_bell = bell_map["pytket"]()
qasm2_bell = bell_map["qasm2"]()


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

    _, err = capfd.readouterr()
    assert len(err) == 0


def test_braket_raises():
    """Test that drawing braket circuit with non-supported output raises error"""
    with pytest.raises(VisualizationError):
        circuit_drawer(braket_bell, output="bad_input")


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"])
def test_cirq_bell_text_draw(capfd, package):
    """Test using Cirq to draw circuit using text output is of the expected length."""
    # pylint: disable=eval-used
    circuit_wrapper(eval(f"{package}_bell")).draw(package="cirq", output="text")

    _, err = capfd.readouterr()
    assert len(err) == 0


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

    _, err = capfd.readouterr()
    assert len(err) == 0


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
