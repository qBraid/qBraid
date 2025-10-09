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

# pylint: disable=unused-import

"""
Fixtures imported/defined in this file can be used by any test in this directory
without needing to import them (pytest will automatically discover them).

"""
import importlib.util
import os
import sys

import pytest

from .fixtures import bell_circuit as bell_circuit
from .fixtures import bell_unitary as bell_unitary
from .fixtures import packages_bell as packages_bell
from .fixtures import packages_shared15 as packages_shared15
from .fixtures import shared15_circuit as shared15_circuit
from .fixtures import shared15_unitary as shared15_unitary
from .fixtures import two_bell_circuits as two_bell_circuits
from .fixtures import two_shared15_circuits as two_shared15_circuits


def _is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


@pytest.fixture
def available_targets():
    """Return a list of available quantum packages."""
    packages = ["braket", "cirq", "pytket", "qiskit", "pyquil"]

    # Add version-restricted packages only if Python version is compatible
    if sys.version_info < (3, 12):
        packages.extend(["pyqubo"])
    if sys.version_info < (3, 13):
        packages.extend(["bloqade"])

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
