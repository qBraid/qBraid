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

# pylint: disable=redefined-outer-name,unused-argument

"""
Unit tests for runtime display functions.

"""
from unittest.mock import patch

from qbraid.runtime._display import display_jobs_from_data


def test_empty_table():
    """Test displaying an empty table."""
    data = {}
    with patch("builtins.print") as mock_print:
        display_jobs_from_data(data)
        actual_print_args = " ".join([str(arg[0]) for arg in mock_print.call_args_list])
        assert "No jobs found matching criteria." in actual_print_args


def test_nonempty_table():
    """Test displaying a nonempty table."""
    data = [("1", "2", "3")]
    with patch("builtins.print") as mock_print:
        display_jobs_from_data(data)
        actual_print_args = " ".join([str(arg[0]) for arg in mock_print.call_args_list])
        assert "Displaying 1 job." in actual_print_args
