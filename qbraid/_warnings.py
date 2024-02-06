# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for emitting and disabling warnings at top level.

"""
import warnings
from importlib.metadata import PackageNotFoundError, version

import requests
import urllib3

from .exceptions import QbraidError


def _get_latest_version(package: str) -> str:
    """Retrieves the latest version of a package from PyPI."""
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except requests.RequestException as err:
        raise QbraidError(f"Failed to retrieve latest {package} version.") from err


def _get_local_version(package: str) -> str:
    """Retrieves the local version of a package."""
    try:
        return version(package)
    except PackageNotFoundError as err:
        raise QbraidError(f"{package} is not installed in the current environment.") from err


def _warn_new_version(local: str, latest: str) -> bool:
    """Returns True if you should warn user about updated package version,
    False otherwise."""
    installed_major, installed_minor = map(int, local.split(".")[:2])
    latest_major, latest_minor = map(int, latest.split(".")[:2])

    return (installed_major, installed_minor) < (latest_major, latest_minor)


def _check_version():
    """Emits UserWarning if updated package version exists in qBraid API
    compared to local copy."""

    # pylint: disable=import-outside-toplevel
    try:
        latest_version = _get_latest_version("qbraid")
        local_version = _get_local_version("qbraid")

        if _warn_new_version(local_version, latest_version):
            warnings.warn(
                f"You are using qbraid version {local_version}; however, version {latest_version} "
                "is available. To avoid compatibility issues, consider upgrading. ",
                UserWarning,
            )
    except QbraidError:
        pass


# coverage: ignore
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning, message="Setuptools is replacing distutils")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_check_version()
