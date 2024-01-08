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
Unit tests for adding new conversions to the conversion graph

"""
import braket.circuits
import pytest
from qiskit_braket_provider.providers.adapter import convert_qiskit_to_braket_circuit

from qbraid.interface import ConversionEdge, ConversionGraph
from qbraid.interface.converter import convert_to_package


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_initialize_new_conversion(bell_circuit):
    """Test initializing the conversion graph with a new conversion"""
    qiskit_circuit, _ = bell_circuit
    conversions = [
        ConversionEdge(
            "qiskit",
            "braket",
            convert_qiskit_to_braket_circuit,
        )
    ]
    graph = ConversionGraph(conversions)
    assert len(graph.edges) == 1
    braket_circuit = convert_to_package(qiskit_circuit, "braket", conversion_graph=graph)
    assert isinstance(braket_circuit, braket.circuits.Circuit)


@pytest.mark.parametrize("bell_circuit", ["qiskit"], indirect=True)
def test_overwrite_new_conversion(bell_circuit):
    """Test dynamically adding a new conversion  the conversion graph"""
    qiskit_circuit, _ = bell_circuit
    conversions = [ConversionEdge("qiskit", "braket", lambda x: x)]
    graph = ConversionGraph(conversions)
    assert len(graph.edges) == 1
    edge = ConversionEdge("qiskit", "braket", convert_qiskit_to_braket_circuit)
    graph.add_conversion(edge, overwrite=True)
    assert len(graph.edges) == 1
    braket_circuit = convert_to_package(qiskit_circuit, "braket", conversion_graph=graph)
    assert isinstance(braket_circuit, braket.circuits.Circuit)
