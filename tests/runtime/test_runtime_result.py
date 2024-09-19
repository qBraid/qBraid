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
Unit tests for the Result class.

"""

import datetime

import pytest

from qbraid.runtime.enums import ExperimentType
from qbraid.runtime.result import GateModelResultData, Result


@pytest.fixture
def result_instance():
    """Fixture to create a Result object for testing."""
    return Result(
        device_id="test_device",
        job_id="test_job",
        success=True,
        data=GateModelResultData(),
        test_detail="test_value",
    )


def test_format_value_string(result_instance):
    """Test _format_value with a string input."""
    assert result_instance._format_value("hello") == "'hello'"


def test_format_value_enum(result_instance):
    """Test _format_value with an Enum input."""
    assert result_instance._format_value(ExperimentType.GATE_MODEL) == "GATE_MODEL"


def test_format_value_datetime(result_instance):
    """Test _format_value with a datetime input."""
    test_datetime = datetime.datetime(2023, 1, 1, 12, 0)
    assert result_instance._format_value(test_datetime) == "2023-01-01T12:00:00Z"


def test_format_value_dict(result_instance):
    """Test _format_value with a dict input."""
    test_dict = {"key1": "value1", "key2": "value2"}
    assert result_instance._format_value(test_dict) == "{key1: 'value1', key2: 'value2'}"


def test_format_value_dict_with_depth(result_instance):
    """Test _format_value with a nested dict input and depth limit."""
    test_dict = {"key1": {"nested_key": "nested_value"}}
    assert result_instance._format_value(test_dict, depth=2) == "{...}"


def test_format_value_list(result_instance):
    """Test _format_value with a list input."""
    test_list = ["item1", "item2", "item3"]
    assert result_instance._format_value(test_list) == "['item1', 'item2', 'item3']"


def test_format_value_list_with_depth(result_instance):
    """Test _format_value with a nested list and depth limit."""
    test_list = [["item1", "item2"], ["item3", "item4"]]
    assert result_instance._format_value(test_list, depth=2) == "[...]"


def test_repr(result_instance):
    """Test __repr__ method of Result class."""
    expected_repr = (
        "Result(\n"
        "  device_id=test_device,\n"
        "  job_id=test_job,\n"
        "  success=True,\n"
        "  data=GateModelResultData(measurement_counts=None, measurements=None)"
    )
    assert repr(result_instance).startswith(expected_repr)
