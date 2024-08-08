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
Configurations for pyquil tests.

"""

import importlib.util

import pytest


def is_pyquil_installed():
    """Check if the 'pyquil' package is installed."""
    pyquil_spec = importlib.util.find_spec("pyquil")
    return pyquil_spec is not None


# pylint: disable-next=unused-argument
def pytest_collection_modifyitems(config, items):
    """Skip tests if 'pyquil' is not installed."""
    if not is_pyquil_installed():
        skip_marker = pytest.mark.skip(reason="pyquil is not installed.")
        for item in items:
            item.add_marker(skip_marker)
