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
Unit tests for circuit drawer

# TODO: shared15 draw testcase, after fixing circuit decomposition problem from cirq

"""
import importlib.util

import pytest

from qbraid.programs import ProgramTypeError, load_program
from qbraid.visualization.draw_circuit import circuit_drawer


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = ["braket", "cirq", "qiskit", "pytket", "pyquil"]
AVAILABLE_TARGETS = [pkg for pkg in ALL_TARGETS if is_package_installed(pkg)] + ["qasm2"]


def test_draw_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer("bad_input")


def test_draw_program_raises():
    """Test that non-supported package raises error"""
    with pytest.raises(ProgramTypeError):
        circuit_drawer(None)


@pytest.mark.skipif("qiskit" not in AVAILABLE_TARGETS, reason="qiskit not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_draw(bell_circuit):
    """Test draw function standard output for qiskit bell circuit."""
    expected = """          ┌───┐
q_0: ─────┤ X ├
     ┌───┐└─┬─┘
q_1: ┤ H ├──■──
     └───┘     """
    qiskit_bell, _ = bell_circuit
    qprogram = load_program(qiskit_bell)
    qprogram.reverse_qubit_order()
    result = circuit_drawer(qprogram.program, output="text")
    assert str(result) == expected


@pytest.mark.skipif("braket" not in AVAILABLE_TARGETS, reason="braket not installed")
@pytest.mark.parametrize("bell_circuit", AVAILABLE_TARGETS, indirect=True)
def test_braket_bell_draw(capfd, bell_circuit):
    """Test using Amazon Braket to draw using ascii output is of the expected length."""
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="braket", output="ascii")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.skipif("braket" not in AVAILABLE_TARGETS, reason="braket not installed")
@pytest.mark.parametrize("bell_circuit", ["braket"], indirect=True)
def test_braket_raises(bell_circuit):
    """Test that drawing braket circuit with non-supported output raises error"""
    braket_bell, _ = bell_circuit
    with pytest.raises(ValueError):
        circuit_drawer(braket_bell, output="bad_input")


@pytest.mark.skipif("cirq" not in AVAILABLE_TARGETS, reason="cirq not installed")
@pytest.mark.parametrize("bell_circuit", AVAILABLE_TARGETS, indirect=True)
def test_cirq_bell_text_draw(capfd, bell_circuit):
    """Test using Cirq to draw circuit using text output is of the expected length."""
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="cirq", output="text")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.skipif("cirq" not in AVAILABLE_TARGETS, reason="cirq not installed")
@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
def test_cirq_bell_svg_draw(bell_circuit):
    """Test drawing Cirq circuit using SVG source output"""
    cirq_bell, _ = bell_circuit
    svg_str = circuit_drawer(cirq_bell, output="svg_source")
    assert svg_str.startswith("<svg") and svg_str.endswith("</svg>")


@pytest.mark.skipif("cirq" not in AVAILABLE_TARGETS, reason="cirq not installed")
@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
def test_cirq_raises(bell_circuit):
    """Test that drawing Cirq circuit with non-supported output raises error"""
    cirq_bell, _ = bell_circuit
    with pytest.raises(ValueError):
        circuit_drawer(cirq_bell, output="bad_input")


@pytest.mark.skipif("pyquil" not in AVAILABLE_TARGETS, reason="pyquil not installed")
@pytest.mark.parametrize("bell_circuit", AVAILABLE_TARGETS, indirect=True)
def test_pyquil_bell_draw(capfd, bell_circuit):
    """Test using pyquil to draw circuit using text output is of the expected length."""
    circuit, _ = bell_circuit
    circuit_drawer(circuit, as_package="pyquil", output="text")

    _, err = capfd.readouterr()
    assert len(err) == 0


@pytest.mark.skipif("pyquil" not in AVAILABLE_TARGETS, reason="pyquil not installed")
@pytest.mark.parametrize("bell_circuit", ["pyquil"], indirect=True)
def test_pyquil_raises(bell_circuit):
    """Test that drawing pyQuil program with non-supported output raises error"""
    pyquil_bell, _ = bell_circuit
    with pytest.raises(ValueError):
        circuit_drawer(pyquil_bell, output="bad_input")


@pytest.mark.skipif("pytket" not in AVAILABLE_TARGETS, reason="pytket not installed")
@pytest.mark.parametrize("bell_circuit", ["pytket"], indirect=True)
def test_pytket_draw(bell_circuit):
    """Test draw function html output for pytket bell circuit."""
    pytket_bell, _ = bell_circuit
    raw_html: str = circuit_drawer(pytket_bell, output="html")
    assert 2381 <= len(raw_html) <= 4469


@pytest.mark.skipif("pytket" not in AVAILABLE_TARGETS, reason="pytket not installed")
@pytest.mark.parametrize("bell_circuit", ["pytket"], indirect=True)
def test_pytket_raises(bell_circuit):
    """Test that drawing pytket circuit with non-supported output raises error"""
    pytket_bell, _ = bell_circuit
    with pytest.raises(ValueError):
        circuit_drawer(pytket_bell, output="bad_input")
