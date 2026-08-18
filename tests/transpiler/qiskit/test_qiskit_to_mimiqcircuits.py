# Copyright 2026 qBraid
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
Unit tests for the ``qiskit -> mimiq`` conversion and the ``mimiq`` transpiler node.

Requires the optional ``qperfect`` extra (``mimiqcircuits`` + ``mimiq-qiskit``).
"""

import pytest

pytest.importorskip("mimiqcircuits")
pytest.importorskip("mimiq_qiskit")

# pylint: disable=wrong-import-position
import mimiqcircuits as mc
from qiskit import QuantumCircuit

from qbraid.programs import get_program_type_alias, load_program
from qbraid.programs.gate_model.mimiqcircuits import MimiqProgram
from qbraid.transpiler import ConversionGraph
from qbraid.transpiler.conversions.qiskit.qiskit_to_mimiqcircuits import qiskit_to_mimiqcircuits


def _bell() -> QuantumCircuit:
    """Return a 2-qubit Bell circuit with measurements."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure_all()
    return circuit


def test_qiskit_to_mimiqcircuits_returns_native_circuit():
    """The converter delegates to mimiq-qiskit and yields a native MIMIQ circuit."""
    assert isinstance(qiskit_to_mimiqcircuits(_bell()), mc.Circuit)


def test_conversion_graph_has_qiskit_to_mimiqcircuits_edge():
    """``mimiq`` is a registered node reachable from qiskit."""
    graph = ConversionGraph()
    assert graph.has_node("mimiqcircuits")
    assert graph.has_edge("qiskit", "mimiqcircuits")
    assert graph.has_path("qiskit", "mimiqcircuits")


def test_native_mimiq_resolves_to_mimiq_alias():
    """A native MIMIQ circuit is recognized as the ``mimiq`` program type."""
    assert get_program_type_alias(qiskit_to_mimiqcircuits(_bell())) == "mimiqcircuits"


def test_load_program_wraps_mimiq_circuit():
    """``load_program`` wraps a native MIMIQ circuit in ``MimiqProgram``."""
    program = load_program(qiskit_to_mimiqcircuits(_bell()))
    assert isinstance(program, MimiqProgram)
    assert program.num_qubits == 2
