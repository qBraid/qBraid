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
Configures the logging for the qBraid-SDK.

The log level is set based on the `LOG_LEVEL` environment variable, which can be a string
(e.g., "DEBUG", "INFO") or an integer (e.g., 10 for DEBUG). If an invalid value is provided,
the log level defaults to `WARNING`, and a warning is logged.

Format: `%(levelname)s - %(message)s`

Usage:
    from qbraid._logging import logger

Environment Variables:
    LOG_LEVEL: The desired log level (default: INFO).
"""

import logging
import os

VALID_LOG_LEVELS = {logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}
DEFAULT_LOG_LEVEL = logging.WARNING


def get_log_level_from_env():
    """Get the log level from the LOG_LEVEL environment variable, or default to WARNING."""
    log_level_env = os.getenv("LOG_LEVEL", "")

    if log_level_env.isdigit():
        log_level = int(log_level_env)
        if log_level in VALID_LOG_LEVELS:
            return log_level

        logging.warning(
            "Invalid log level (int) in LOG_LEVEL: %s. Falling back to WARNING.", log_level
        )
        return DEFAULT_LOG_LEVEL

    log_level_str = log_level_env.upper()
    log_level = getattr(logging, log_level_str, None)

    if log_level in VALID_LOG_LEVELS:
        return log_level

    if log_level_env:
        logging.warning(
            "Invalid log level (str) in LOG_LEVEL: %s. Falling back to WARNING.", log_level_env
        )

    return DEFAULT_LOG_LEVEL


logging.basicConfig(format="%(levelname)s - %(message)s", level=get_log_level_from_env())

logger = logging.getLogger(__name__)


__all__ = ["logger", "DEFAULT_LOG_LEVEL", "VALID_LOG_LEVELS"]
