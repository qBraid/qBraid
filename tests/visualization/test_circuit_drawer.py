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
from qbraid.exceptions import ProgramTypeError
from qbraid.visualization.draw_circuit import circuit_drawer
from qbraid.visualization.exceptions import VisualizationError


def test_draw_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer("bad_input")


def test_draw_program_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer(None)


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_draw(bell_circuit):
    """Test draw function standard output for qiskit bell circuit."""
    expected = """          ┌───┐
q_0: ─────┤ X ├
     ┌───┐└─┬─┘
q_1: ┤ H ├──■──
     └───┘     """
    qiskit_bell, _ = bell_circuit
    qprogram = circuit_wrapper(qiskit_bell)
    qprogram.reverse_qubit_order()
    result = circuit_drawer(qprogram.program, output="text")
    assert str(result) == expected


@pytest.mark.parametrize(
    "bell_circuit", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"], indirect=True
)
def test_braket_bell_draw(capfd, bell_circuit):
    """Test using Amazon Braket to draw using ascii output is of the expected length."""
    # pylint: disable=eval-used
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="braket", output="ascii")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.parametrize("bell_circuit", ["braket"], indirect=True)
def test_braket_raises(bell_circuit):
    """Test that drawing braket circuit with non-supported output raises error"""
    braket_bell, _ = bell_circuit
    with pytest.raises(VisualizationError):
        circuit_drawer(braket_bell, output="bad_input")


@pytest.mark.parametrize(
    "bell_circuit", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"], indirect=True
)
def test_cirq_bell_text_draw(capfd, bell_circuit):
    """Test using Cirq to draw circuit using text output is of the expected length."""
    # pylint: disable=eval-used
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="cirq", output="text")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
def test_cirq_bell_svg_draw(bell_circuit):
    """Test drawing Cirq circuit using SVG source output"""
    cirq_bell, _ = bell_circuit
    svg_str = circuit_drawer(cirq_bell, output="svg_source")
    assert svg_str.startswith("<svg") and svg_str.endswith("</svg>")


@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
def test_cirq_raises(bell_circuit):
    """Test that drawing Cirq circuit with non-supported output raises error"""
    cirq_bell, _ = bell_circuit
    with pytest.raises(VisualizationError):
        circuit_drawer(cirq_bell, output="bad_input")


@pytest.mark.parametrize(
    "bell_circuit", ["braket", "cirq", "qiskit", "pytket", "pyquil", "qasm2"], indirect=True
)
def test_pyquil_bell_draw(capfd, bell_circuit):
    """Test using pyquil to draw circuit using text output is of the expected length."""
    # pylint: disable=eval-used
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="pyquil", output="text")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.parametrize("bell_circuit", ["pyquil"], indirect=True)
def test_pyquil_raises(bell_circuit):
    """Test that drawing pyQuil program with non-supported output raises error"""
    pyquil_bell, _ = bell_circuit
    with pytest.raises(VisualizationError):
        circuit_drawer(pyquil_bell, output="bad_input")


@pytest.mark.parametrize("bell_circuit", ["pytket"], indirect=True)
def test_pytket_draw(bell_circuit):
    """Test draw function html output for pytket bell circuit."""
    pytket_bell, _ = bell_circuit
    assert len(circuit_drawer(pytket_bell, output="html")) == 2381


@pytest.mark.parametrize("bell_circuit", ["pytket"], indirect=True)
def test_pytket_raises(bell_circuit):
    """Test that drawing pytket circuit with non-supported output raises error"""
    pytket_bell, _ = bell_circuit
    with pytest.raises(VisualizationError):
        circuit_drawer(pytket_bell, output="bad_input")
