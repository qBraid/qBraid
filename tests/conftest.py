# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=unused-import

"""
Fixtures imported/defined in this file can be used by any test in this directory
without needing to import them (pytest will automatically discover them).

"""
import importlib.util
import os

import pytest

from .fixtures import (
    bell_circuit,
    bell_unitary,
    packages_bell,
    packages_shared15,
    shared15_circuit,
    shared15_unitary,
    two_bell_circuits,
    two_shared15_circuits,
)


def _is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


@pytest.fixture
def available_targets():
    """Return a list of available quantum packages."""
    packages = ["braket", "cirq", "pyquil", "pytket", "qiskit"]
    return [pkg for pkg in packages if _is_package_installed(pkg)]


def pytest_addoption(parser):
    """Adds custom remote testing command-line option to pytest."""
    parser.addoption(
        "--remote",
        action="store",
        default=None,
        help="Run tests that interface with remote, credentialed services: true or false",
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked with `remote` if remote tests are disabled."""
    remote_option = config.getoption("--remote")
    if remote_option is None:
        remote_option = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() == "true"
    else:
        remote_option = remote_option.lower() == "true"

    if not remote_option:
        skip_remote = pytest.mark.skip(reason="Remote tests are disabled.")
        for item in items:
            if "remote" in item.keywords:
                item.add_marker(skip_remote)


@pytest.fixture(autouse=True)
def disable_cache_for_tests(monkeypatch):
    """Disable caching for all tests."""
    monkeypatch.setenv("DISABLE_CACHE", "1")
