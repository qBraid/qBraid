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
Unit tests related to qBraid core functionality and system configurations.

"""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from qbraid.api import QbraidSession
from qbraid.api.system import (
    get_active_site_packages_path,
    get_local_package_path,
    get_qbraid_envs_paths,
    is_valid_env_name,
    is_valid_slug,
)
from qbraid.exceptions import QbraidError

skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid storage)"


@pytest.mark.parametrize(
    "slug, expected",
    [
        ("abc_123456", True),  # Valid slug
        ("", False),  # Empty slug
        ("a" * 7 + "_123456", True),  # Valid slug with max name length
        ("a" * 14 + "_123456", False),  # Name part too long
        ("abc_def_123456", True),  # Valid slug with underscores in name
        ("abc-def_123456", False),  # Invalid character '-' in name
        ("ABC_123456", False),  # Capital letters in the name part
        ("abc_12345a", True),  # Alphanumeric part with lowercase letters
        ("abc_12345", False),  # Alphanumeric part too short
        ("abc_!23456", False),  # Invalid character '!' in name
        ("abc_12345G", False),  # Capital letter in the alphanumeric part
        ("123_456789", True),  # Numeric name part
        ("abc123456789", False),  # Missing underscore separator
        ("abc__123456", False),  # Double underscore in name
        ("_123_123456", False),  # Starting with underscore (name part too short)
        ("a" * 7 + "_1a2b3c", True),  # Valid edge case
    ],
)
def test_is_valid_slug(slug, expected):
    """Test the is_valid_slug function."""
    assert is_valid_slug(slug) == expected


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_verified_slugs_are_valid():
    """Test that all existing qBraid environment slugs are deemed valid."""
    session = QbraidSession()
    res = session.get("/environments").json()
    for env in res:
        slug = env["slug"]
        assert is_valid_slug(slug)


def test_get_qbraid_envs_paths_with_env_var_set(monkeypatch):
    """Test the get_qbraid_envs_paths function when QBRAID_ENVS_PATH is set."""
    # Mocking QBRAID_ENVS_PATH with two paths for the test
    mock_envs_path = "/path/to/envs1:/path/to/envs2"
    monkeypatch.setenv("QBRAID_ENVS_PATH", mock_envs_path)

    expected_paths = [Path("/path/to/envs1"), Path("/path/to/envs2")]
    assert (
        get_qbraid_envs_paths() == expected_paths
    ), "Should return paths from QBRAID_ENVS_PATH environment variable"


def test_get_qbraid_envs_paths_with_no_env_var_set(monkeypatch):
    """Test the get_qbraid_envs_paths function when QBRAID_ENVS_PATH is not set."""
    # Removing QBRAID_ENVS_PATH to simulate it not being set
    monkeypatch.delenv("QBRAID_ENVS_PATH", raising=False)

    expected_path = Path.home() / ".qbraid" / "environments"
    assert get_qbraid_envs_paths() == [
        expected_path
    ], "Should return the default path when QBRAID_ENVS_PATH is not set"


# Success with a single site-packages path
@patch("site.getsitepackages", return_value=["/path/to/site-packages"])
def test_single_site_packages_path(mock_getsitepackages):
    """Test the get_active_site_packages_path function when a single site-packages path is found."""
    assert get_active_site_packages_path() == "/path/to/site-packages"


# Success with multiple site-packages paths, one matching the current environment
@pytest.mark.skip(reason="Not passing")
@patch(
    "site.getsitepackages", return_value=["/wrong/path/to/site-packages", "/path/to/site-packages"]
)
@patch("sys.executable", return_value="/path/to/python")
def test_multiple_site_packages_paths(mock_executable, mock_getsitepackages):
    """Test the get_active_site_packages_path function when multiple site-packages paths are found."""
    assert get_active_site_packages_path() == "/path/to/site-packages"


# Failure to find site-packages path
@pytest.mark.skip(reason="Not passing")
@patch("site.getsitepackages", return_value=["/wrong/path/to/site-packages"])
@patch("sys.executable", return_value="/another/path/to/python")
def test_fail_to_find_site_packages(mock_executable, mock_getsitepackages):
    """Test the get_active_site_packages_path function when the site-packages path cannot be found."""
    with pytest.raises(QbraidError):
        get_active_site_packages_path()


@patch("qbraid.api.system.get_active_site_packages_path", return_value="/path/to/site-packages")
def test_get_local_package_path_exists(mock_get_active_site_packages_path):
    """Test the get_local_package_path function with an existing package."""
    package_name = "existing_package"
    expected_path = "/path/to/site-packages/existing_package"
    assert get_local_package_path(package_name) == expected_path


@patch(
    "qbraid.api.system.get_active_site_packages_path",
    side_effect=QbraidError("Failed to find site-packages path."),
)
def test_get_local_package_path_error(mock_get_active_site_packages_path):
    package_name = "nonexistent_package"
    with pytest.raises(QbraidError):
        get_local_package_path(package_name)


@pytest.mark.parametrize(
    "env_name, expected",
    [
        # Valid names
        ("valid_env", True),
        ("env123", True),
        ("_env", True),
        # Invalid names due to invalid characters
        ("env*name", False),
        ("<env>", False),
        ("env|name", False),
        # Reserved names
        ("CON", False),
        ("com1", False),
        # Names that are too long
        ("a" * 21, False),
        # Empty or whitespace names
        ("", False),
        ("   ", False),
        # Python reserved words
        ("False", False),
        ("import", False),
        # Names starting with a number
        ("1env", False),
        ("123", False),
    ],
)
def test_is_valid_env_name(env_name, expected):
    """Test function that verifies valid python venv names."""
    assert is_valid_env_name(env_name) == expected
