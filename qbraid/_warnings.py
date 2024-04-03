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

from qbraid_core._warnings import _check_version


def _filterwarnings():
    """Filter out warnings that are not relevant to the user."""
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    warnings.filterwarnings(
        "ignore", category=UserWarning, message="Setuptools is replacing distutils"
    )
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    # warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="numpy")


def _warn_version():
    """Emit a warning."""
    _check_version("qbraid")


_warn_version()
_filterwarnings()
