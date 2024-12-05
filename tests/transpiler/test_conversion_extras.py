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
