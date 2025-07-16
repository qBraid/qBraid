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
Tests for qBraid transpiler conversion extras.

"""
import importlib.util
from typing import Callable

import braket.circuits
import pytest

try:
    import pyqir

    pyqir_installed = True
except ImportError:
    pyqir_installed = False


from qbraid.passes.qasm.compat import normalize_qasm_gate_params
from qbraid.transpiler.conversions.qasm3 import autoqasm_to_qasm3
from qbraid.transpiler.conversions.qiskit import qiskit_to_braket, qiskit_to_pyqir
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph


def has_extra(conversion_func: Callable) -> bool:
    """
    Check if the conversion function requires extra packages.

    Args:
        conversion_func (Callable): The conversion function to check for extra requirements.

    Returns:
        bool: True if all required extra packages are importable, False otherwise.
    """
    extras = getattr(conversion_func, "requires_extras", [])
    return all(importlib.util.find_spec(module_name) is not None for module_name in extras)


@pytest.mark.skipif(not has_extra(qiskit_to_braket), reason="Extra not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_to_braket_extra(bell_circuit):
    """Test qiskit-braket-provider transpiler conversion extra."""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "braket", qiskit_to_braket)]
    graph = ConversionGraph(conversions)
    program = transpile(qiskit_circuit, "braket", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, braket.circuits.Circuit)


@pytest.mark.skipif(not has_extra(qiskit_to_pyqir), reason="Extra not installed")
@pytest.mark.skipif(not pyqir_installed, reason="pyqir not installed")
@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_qiskit_to_pyqir_extra(bell_circuit):
    """Test qiskit-qir transpiler conversion extra."""
    qiskit_circuit, _ = bell_circuit
    conversions = [Conversion("qiskit", "pyqir", qiskit_to_pyqir)]
    graph = ConversionGraph(conversions)
    program = transpile(qiskit_circuit, "pyqir", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, pyqir.Module)


def autoqasm_bell_circuit():
    """Function that returns autoqasm bell circuit."""
    # pylint: disable-next=import-outside-toplevel
    from ..fixtures.autoqasm.circuits import autoqasm_bell

    return autoqasm_bell()


def qasm3_bell_reference():
    """Reference QASM3 string for Bell circuit"""
    return """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] __qubits__;
h __qubits__[0];
cx __qubits__[0], __qubits__[1];"""


@pytest.mark.skipif(not has_extra(autoqasm_to_qasm3), reason="Extra not installed")
def test_autoqasm_bell_to_qasm3_extra():
    """Test autoqasm-qasm3 conversion extra."""
    autoqasm_circuit = autoqasm_bell_circuit()
    conversions = [Conversion("autoqasm", "qasm3", autoqasm_to_qasm3)]
    graph = ConversionGraph(conversions)
    program = transpile(autoqasm_circuit, "qasm3", conversion_graph=graph, max_path_depth=1)
    assert isinstance(program, str)
    assert program == qasm3_bell_reference()


def autoqasm_shared15_circuit():
    """Function that returns autoqasm shared15 circuit."""
    # pylint: disable-next=import-outside-toplevel
    from ..fixtures.autoqasm.circuits import autoqasm_shared15

    return autoqasm_shared15()


def qasm3_shared15_reference():
    """Reference QASM3 string for shared15 circuit"""
    return """OPENQASM 3.0;
include "stdgates.inc";
gate sxdg _gate_q_0 {
  s _gate_q_0;
  h _gate_q_0;
  s _gate_q_0;
}
gate iswap _gate_q_0, _gate_q_1 {
  s _gate_q_0;
  s _gate_q_1;
  h _gate_q_0;
  cx _gate_q_0, _gate_q_1;
  cx _gate_q_1, _gate_q_0;
  h _gate_q_1;
}
qubit[4] __qubits__;
h __qubits__[0];
h __qubits__[1];
h __qubits__[2];
h __qubits__[3];
x __qubits__[0];
x __qubits__[1];
y __qubits__[2];
z __qubits__[3];
s __qubits__[0];
sdg __qubits__[1];
t __qubits__[2];
tdg __qubits__[3];
rx(pi/4) __qubits__[0];
ry(pi/2) __qubits__[1];
rz(3*pi/4) __qubits__[2];
p(pi/8) __qubits__[3];
sx __qubits__[0];
sxdg __qubits__[1];
iswap __qubits__[2], __qubits__[3];
swap __qubits__[0], __qubits__[2];
swap __qubits__[1], __qubits__[3];
cx __qubits__[0], __qubits__[1];
cp(pi/4) __qubits__[2], __qubits__[3];"""


@pytest.mark.skipif(not has_extra(autoqasm_to_qasm3), reason="Extra not installed")
def test_autoqasm_shared15_to_qasm3_extra():
    """Test autoqasm-qasm3 conversion extra."""
    autoqasm_circuit = autoqasm_shared15_circuit()
    conversions = [Conversion("autoqasm", "qasm3", autoqasm_to_qasm3)]
    graph = ConversionGraph(conversions)
    program = transpile(autoqasm_circuit, "qasm3", conversion_graph=graph, max_path_depth=1)

    assert isinstance(program, str)
    assert program == normalize_qasm_gate_params(qasm3_shared15_reference())
