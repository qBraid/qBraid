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

"""Unit tests for myQLM (qat) extras-based conversion functions."""

# pylint: disable=import-outside-toplevel

import importlib.util
from typing import Callable

import pytest

from qbraid.transpiler.conversions.qasm2.qasm2_extras import qasm2_to_qat
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph

try:
    from qbraid.transpiler.conversions.cirq.cirq_extras import cirq_to_qat
except (ImportError, ModuleNotFoundError):
    cirq_to_qat = None  # type: ignore[assignment]


def has_extra(conversion_func: Callable) -> bool:
    """Check if all required extras for a conversion function are importable."""
    if conversion_func is None:
        return False
    extras = getattr(conversion_func, "requires_extras", [])
    if not extras:
        return False
    try:
        return all(importlib.util.find_spec(m) is not None for m in extras)
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


BELL_QASM2 = """\
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
"""


# ---------------------------------------------------------------------------
# qasm2_to_qat
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(qasm2_to_qat), reason="Extra not installed")
def test_qasm2_to_qat_returns_circuit():
    """qasm2_to_qat should return a qat Circuit object."""
    from qat.core import Circuit as QatCircuit

    result = qasm2_to_qat(BELL_QASM2)
    assert isinstance(result, QatCircuit)


@pytest.mark.skipif(not has_extra(qasm2_to_qat), reason="Extra not installed")
def test_qasm2_to_qat_bell_gates():
    """Bell circuit should contain H and CNOT gates after conversion."""
    result = qasm2_to_qat(BELL_QASM2)
    gate_names = [g[0] for g in result.iterate_simple()]
    assert "H" in gate_names
    assert "CNOT" in gate_names


@pytest.mark.skipif(not has_extra(qasm2_to_qat), reason="Extra not installed")
def test_qasm2_to_qat_graph_reachable():
    """qasm2 to qat edge should be discoverable via ConversionGraph."""
    graph = ConversionGraph(conversions=[Conversion("qasm2", "qat", qasm2_to_qat)])
    assert "qat" in graph.nodes()


# ---------------------------------------------------------------------------
# cirq_to_qat
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(cirq_to_qat), reason="Extra not installed")
def test_cirq_to_qat_returns_circuit():
    """cirq_to_qat should return a qat Circuit."""
    import cirq
    from qat.core import Circuit as QatCircuit

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    result = cirq_to_qat(circuit)
    assert isinstance(result, QatCircuit)


@pytest.mark.skipif(not has_extra(cirq_to_qat), reason="Extra not installed")
def test_cirq_to_qat_graph_reachable():
    """cirq to qat edge should be discoverable via ConversionGraph."""
    graph = ConversionGraph(conversions=[Conversion("cirq", "qat", cirq_to_qat)])
    assert "qat" in graph.nodes()


# ---------------------------------------------------------------------------
# Auto-discovery via default ConversionGraph (wiring regression guard)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not has_extra(qasm2_to_qat), reason="Extra not installed")
def test_qasm2_to_qat_auto_discovered():
    """qasm2_to_qat should appear in conversion_functions via dynamic discovery."""
    from qbraid.transpiler.conversions import conversion_functions

    assert "qasm2_to_qat" in conversion_functions


@pytest.mark.skipif(not has_extra(qasm2_to_qat), reason="Extra not installed")
def test_qat_node_in_default_graph():
    """qat should be a node in the default ConversionGraph when myqlm-interop is installed."""
    graph = ConversionGraph()
    assert "qat" in graph.nodes()


# ---------------------------------------------------------------------------
# requires_extras attributes
# ---------------------------------------------------------------------------


def test_qasm2_to_qat_requires_extras_attribute():
    """qasm2_to_qat must declare extras as importable module names."""
    assert hasattr(qasm2_to_qat, "requires_extras")
    assert "qat.interop.openqasm" in qasm2_to_qat.requires_extras


def test_cirq_to_qat_requires_extras_attribute():
    """cirq_to_qat must declare extras as importable module names."""
    if not has_extra(cirq_to_qat):
        pytest.skip("cirq extras not available")
    assert hasattr(cirq_to_qat, "requires_extras")
    assert "qat.interop.cirq" in cirq_to_qat.requires_extras
