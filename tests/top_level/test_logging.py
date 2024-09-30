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
Unit tests for logging configuration.

"""

import logging
import os
from unittest.mock import patch

import pytest

from qbraid._logging import DEFAULT_LOG_LEVEL, get_log_level_from_env


@pytest.mark.parametrize(
    "log_level_env, expected_log_level",
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("debug", logging.DEBUG),
        ("10", logging.DEBUG),
        ("20", logging.INFO),
    ],
)
@patch.dict(os.environ, {}, clear=True)
def test_get_log_level_valid_cases(log_level_env, expected_log_level):
    """Test that valid string or numeric log levels are correctly parsed from the environment."""
    with patch.dict(os.environ, {"LOG_LEVEL": log_level_env}):
        assert get_log_level_from_env() == expected_log_level


@pytest.mark.parametrize(
    "log_level_env, invalid_log_level",
    [
        ("INVALID", "INVALID"),
        ("-1", "-1"),
    ],
)
@patch.dict(os.environ, {}, clear=True)
@patch("logging.warning")
def test_get_log_level_invalid_cases(mock_warning, log_level_env, invalid_log_level):
    """Test that invalid log levels fall back to DEFAULT_LOG_LEVEL and raise a warning."""
    with patch.dict(os.environ, {"LOG_LEVEL": log_level_env}):
        assert get_log_level_from_env() == DEFAULT_LOG_LEVEL
        mock_warning.assert_called_once_with(
            "Invalid log level (str) in LOG_LEVEL: %s. Falling back to WARNING.", invalid_log_level
        )


@patch.dict(os.environ, {}, clear=True)
@patch("logging.warning")
def test_get_log_level_empty_env(mock_warning):
    """Test that when LOG_LEVEL is not set, the function defaults to DEFAULT_LOG_LEVEL."""
    assert get_log_level_from_env() == DEFAULT_LOG_LEVEL
    mock_warning.assert_not_called(), "No warning should be called when the env var is empty"


@patch.dict(os.environ, {}, clear=True)
@patch("logging.warning")
def test_get_log_level_invalid_int_warning(mock_warning):
    """Test that an invalid integer log level falls back to DEFAULT_LOG_LEVEL and logs a warning."""
    with patch.dict(os.environ, {"LOG_LEVEL": "999"}):
        assert get_log_level_from_env() == DEFAULT_LOG_LEVEL
        mock_warning.assert_called_once_with(
            "Invalid log level (int) in LOG_LEVEL: %s. Falling back to WARNING.", 999
        )


@patch.dict(os.environ, {}, clear=True)
def test_get_log_level_valid_int():
    """Test that valid integer log levels are correctly parsed from the environment."""
    with patch.dict(os.environ, {"LOG_LEVEL": "20"}):  # 20 corresponds to INFO
        assert get_log_level_from_env() == logging.INFO


@patch.dict(os.environ, {}, clear=True)
def test_get_log_level_case_insensitive():
    """Test that log levels are case insensitive."""
    with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
        assert get_log_level_from_env() == logging.DEBUG
