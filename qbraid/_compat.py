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
Module for emitting and configuring warnings and logging at top level.

"""
import logging
import os
import warnings

from qbraid_core._compat import check_version


def configure_logging():
    """Configure logging to show warnings and errors."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()  # Default to INFO if not set
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(levelname)s - %(module)s - %(message)s",
    )


def filterwarnings():
    """Filter out warnings that are not relevant to the user."""
    warnings_to_ignore = [
        (SyntaxWarning, None, None),
        (UserWarning, "Setuptools is replacing distutils", None),
        (DeprecationWarning, None, None),
        (RuntimeWarning, None, "numpy"),
        (
            UserWarning,
            "`pydantic.utils:deep_update` has been removed. "
            + "We are importing from `pydantic.v1.utils:deep_update` instead.",
            "pydantic",
        ),
    ]

    for category, message, module in warnings_to_ignore:
        warnings.filterwarnings("ignore", category=category, message=message, module=module)


def check_warn_version_update():
    """Emit a warning if updated qBraid-SDK package version exists."""
    check_version("qbraid")
