# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
