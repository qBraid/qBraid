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
Unit tests for ipython and other display functions.

"""
import logging
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from qbraid._display import running_in_jupyter


class MockIPython:
    """Mock IPython class for testing."""

    def __init__(self, kernel):
        self.kernel = kernel


@pytest.fixture
def mock_ipython(request):
    """Fixture to mock IPython in sys.modules and restore it after the test."""
    kernel_value = request.param
    original_ipython = sys.modules.get("IPython", None)  # Save the original IPython module
    # Create a mock module and assign get_ipython
    mock_module = type("MockModule", (), {})()  # Create a mock module object
    mock_module.get_ipython = Mock(return_value=MockIPython(kernel_value))
    sys.modules["IPython"] = mock_module  # Set the mock module in sys.modules

    yield  # Yield control to the test function

    # Restore the original state after the test
    if original_ipython is not None:
        sys.modules["IPython"] = original_ipython
    else:
        del sys.modules["IPython"]


def test_running_in_jupyter():
    """Test ``running_in_jupyter`` for non-jupyter environment."""
    assert not running_in_jupyter()


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_ipython_imported_but_ipython_none(mock_ipython):
    """Test ``running_in_jupyter`` for IPython imported but ``get_ipython()`` returns None."""
    assert not running_in_jupyter()


@pytest.mark.parametrize("mock_ipython", ["non-empty kernel"], indirect=True)
def test_ipython_imported_and_in_jupyter(mock_ipython):
    """Test ``running_in_jupyter`` for IPython imported and in Jupyter."""
    assert running_in_jupyter()


def test_running_in_jupyter_logs_exception(caplog):
    """
    Test that an exception raised in running_in_jupyter() is logged correctly.
    """
    with patch("sys.modules", new_callable=lambda: {"IPython": MagicMock()}):
        sys.modules["IPython"].__dict__["get_ipython"] = MagicMock(
            side_effect=Exception("Test exception")
        )

        caplog.set_level(logging.ERROR)

        result = running_in_jupyter()

        assert not result, "running_in_jupyter() should return False when an exception occurs"
        assert (
            "Error checking if running in Jupyter: Test exception" in caplog.text
        ), "The exception should be logged as an error"
