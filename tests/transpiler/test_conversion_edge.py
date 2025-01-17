# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for defining custom conversions

"""
from unittest.mock import Mock

import cirq
import numpy as np
import pytest

from qbraid.interface.random import random_circuit
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.transpiler.annotations import requires_extras, weight
from qbraid.transpiler.conversions.braket import braket_to_cirq
from qbraid.transpiler.edge import Conversion
from qbraid.transpiler.graph import ConversionGraph


@requires_extras("alice", "bob")
def dummy_func():
    """Dummy function for testing requires_extras decorator."""


def test_requires_extras_appends_dependency():
    """
    Test that the requires_extras decorator correctly appends a dependency
    to the function's attribute list.
    """
    assert getattr(dummy_func, "requires_extras") == ["alice", "bob"]


def test_raise_for_unsupported_program_input():
    """Test that an exception is raised for an unsupported program input."""
    conversion = Conversion("braket", "cirq", braket_to_cirq)
    circuit = Mock()
    with pytest.raises(ProgramTypeError):
        conversion.convert(circuit)


def test_raise_for_source_program_input_mismatch():
    """Test that an exception is raised for a mismatch between the source package and input."""
    source, target, other = "braket", "cirq", "qiskit"
    conversion = Conversion(source, target, braket_to_cirq)
    circuit = random_circuit(other)
    with pytest.raises(ValueError):
        conversion.convert(circuit)


def test_braket_cirq_custom_conversion():
    """Test that a Braket to Cirq conversion is successful."""
    source, target = "braket", "cirq"
    conversion = Conversion(source, target, braket_to_cirq)
    braket_circuit = random_circuit(source)
    cirq_circuit = conversion.convert(braket_circuit)
    assert isinstance(cirq_circuit, cirq.Circuit)


def test_conversion_repr():
    """Test that the conversion repr is correct."""
    source, target = "braket", "cirq"
    conversion = Conversion(source, target, braket_to_cirq)
    assert repr(conversion) == f"('{source}', '{target}')"


def test_valid_weights():
    """Test that valid weights are applied correctly."""

    @weight(0.5)
    def conversion_function():
        return "Converted"

    assert hasattr(conversion_function, "weight")
    assert conversion_function.weight == 0.5


def test_invalid_weights():
    """Test that weights outside the 0 to 1 range raise a ValueError."""

    with pytest.raises(ValueError) as excinfo:

        @weight(-0.1)
        def negative_weight_function():
            return "Should not work"

    assert "between 0 and 1" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:

        @weight(1.1)
        def too_high_weight_function():
            return "Should not work"

    assert "between 0 and 1" in str(excinfo.value)


def test_functionality():
    """Test that the decorated function works as expected."""

    @weight(1)
    def conversion_function():
        return "Functionality intact"

    assert conversion_function() == "Functionality intact"


def test_default_weight_application():
    """Test the application of a weight at the edge of the valid range."""

    @weight(1)
    def edge_case_function():
        return "Edge case test"

    assert edge_case_function.weight == 1
    assert edge_case_function() == "Edge case test"


@pytest.fixture
def mock_conversion_func():
    """Mock conversion function with a weight attribute."""

    def conversion_function():
        pass

    setattr(conversion_function, "weight", 0.5)

    return conversion_function


@pytest.mark.parametrize("invalid_weight", [-0.1, 1.1])
def test_invalid_weight(mock_conversion_func, invalid_weight):
    """Test initializing with a weight below zero."""
    with pytest.raises(ValueError):
        Conversion("source_pkg", "target_pkg", mock_conversion_func, weight=invalid_weight)


@pytest.mark.parametrize(
    "valid_weight,expected_value", [(0.8, np.log(1.25)), (None, np.log(2)), (0, float("inf"))]
)
def test_valid_weight(mock_conversion_func, valid_weight, expected_value):
    """Test the default weight from the conversion function if not specified."""
    conversion = Conversion("source_pkg", "target_pkg", mock_conversion_func, weight=valid_weight)
    assert conversion.weight == expected_value


def test_weight_without_specified_and_no_default():
    """Test default weight when no weight is specified and no default is in the function."""

    def simple_conversion_func():
        pass  # No weight attribute

    conversion = Conversion("source_pkg", "target_pkg", simple_conversion_func)
    assert conversion.weight == 0


class TestConversionEquality:
    """Tests for the Conversion class __eq__ method."""

    def test_equal_instances(self):
        """Test that two instances with identical initialization are considered equal."""
        conv1 = Conversion("source1", "target1", mock_conversion_func)
        conv2 = Conversion("source1", "target1", mock_conversion_func)
        assert conv1 == conv2, "Instances with identical initialization should be equal"

    def test_unequal_sources(self):
        """Test that instances with different source attributes are not equal."""
        conv1 = Conversion("source1", "target1", mock_conversion_func)
        conv2 = Conversion("source2", "target1", mock_conversion_func)
        assert conv1 != conv2, "Instances with different sources should not be equal"

    def test_unequal_targets(self):
        """Test that instances with different target attributes are not equal."""
        conv1 = Conversion("source1", "target1", mock_conversion_func)
        conv2 = Conversion("source1", "target2", mock_conversion_func)
        assert conv1 != conv2, "Instances with different targets should not be equal"

    def test_unequal_weights(self):
        """Test that instances with different weights are not equal."""
        conv1 = Conversion("source1", "target1", mock_conversion_func, weight=1)
        conv2 = Conversion("source1", "target1", mock_conversion_func, weight=0.6)
        assert conv1 != conv2, "Instances with different weights should not be equal"

    def test_comparison_with_different_type(self):
        """Test that a Conversion instance is not equal to an object of a different type."""
        conv = Conversion("source1", "target1", mock_conversion_func)
        assert (
            conv != "a string"
        ), "Comparison with an object of a different type should return False"


@pytest.mark.parametrize(
    "conversions, start, end, expected_path",
    [
        ([("a", "b", 1.00), ("b", "c", 1.00), ("a", "c", 0.77)], "a", "c", "a -> b -> c"),
        ([("a", "b", 1.00), ("b", "c", 1.00), ("a", "c", 0.78)], "a", "c", "a -> c"),
        (
            [("a", "b", 1.00), ("b", "c", 1.00), ("c", "d", 1.00), ("a", "d", 0.60)],
            "a",
            "d",
            "a -> b -> c -> d",
        ),
        (
            [("a", "b", 1.00), ("b", "c", 1.00), ("c", "d", 1.00), ("a", "d", 0.61)],
            "a",
            "d",
            "a -> d",
        ),
    ],
)
def test_conversion_weight_bias(conversions, start, end, expected_path):
    """Tests the effect of weight biases on determining the shortest path in a conversion graph."""
    conversions = [
        Conversion(src, dst, lambda x: x, weight, bias=0.25) for src, dst, weight in conversions
    ]
    graph = ConversionGraph(conversions=conversions)
    shortest_path = graph.shortest_path(start, end)
    assert shortest_path == expected_path
