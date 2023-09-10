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

import urllib3


def _warn_new_version(local: str, api: str) -> bool:
    """Returns True if you should warn user about updated package version,
    False otherwise."""

    v_local = int("".join(local.split(".")[:3]))
    v_api = int("".join(api.split(".")[:3]))

    if v_local < v_api:
        return True
    return False


def _check_version():
    """Emits UserWarning if updated package version exists in qBraid API
    compared to local copy."""

    # pylint: disable=import-outside-toplevel
    from ._version import __version__ as version_local
    from .api.session import QbraidSession

    session = QbraidSession()

    if not session._running_in_lab():
        return

    version_api = session.get("/public/lab/get-sdk-version", params={}).json()

    if _warn_new_version(version_local, version_api):
        warnings.warn(
            f"You are using qbraid version {version_local}; however, version {version_api} "
            "is available. To avoid compatibility issues, consider upgrading by uninstalling "
            "and reinstalling the qBraid-SDK environment.",
            UserWarning,
        )


# coverage: ignore
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning, message="Setuptools is replacing distutils")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_check_version()
