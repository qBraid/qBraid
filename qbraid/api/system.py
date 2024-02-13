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
Module for gathering system information.

"""

import os
import site
import sys

from qbraid._qdevice import QDEVICE_LIBS
from qbraid.exceptions import QbraidError


def get_site_packages_path() -> str:
    """Retrieves the site-packages path in the current Python environment."""
    site_packages_paths = site.getsitepackages()

    if len(site_packages_paths) == 1:
        return site_packages_paths[0]

    python_executable_path = sys.executable
    env_base_path = os.path.dirname(os.path.dirname(python_executable_path))

    for path in site_packages_paths:
        if env_base_path in path:
            return path

    raise QbraidError("Failed to find site-packages path.")


def _check_proxy(proxy_spec):
    """Checks if qBraid proxy is enabled for a given package and file."""
    package = proxy_spec[0]
    try:
        __import__(package)
    except ImportError:
        return False

    site_packages = get_site_packages_path()
    proxy_filepath = os.path.join(site_packages, *proxy_spec)

    try:
        with open(proxy_filepath, "r", encoding="utf-8") as file:
            for line in file:
                if "qbraid" in line:
                    return True
        return False
    except FileNotFoundError:
        return False
    except Exception:  # pylint: disable=broad-exception-caught
        return False


def qbraid_jobs_enabled(device_lib: str) -> bool:
    """Returns True if qBraid Quantum Jobs are enabled. Otherwise, returns False.

    See https://docs.qbraid.com/projects/lab/en/latest/lab/quantum_jobs.html
    """
    if device_lib not in QDEVICE_LIBS:
        return False

    if device_lib == "braket":
        proxy_spec = ("botocore", "httpsession.py")
    else:
        return False

    return _check_proxy(proxy_spec)
