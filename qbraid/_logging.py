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
    LOG_LEVEL: The desired log level (default: WARNING).
"""

import logging
import os
from typing import Literal

VALID_LOG_LEVELS = {logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}
DEFAULT_LOG_LEVEL = logging.WARNING

LOG_LEVEL_ENV = os.getenv("LOG_LEVEL", "")


def parse_log_level(input_level: str | int | None) -> Literal[10, 20, 30, 40, 50]:
    """Parse the log level from a string or integer and return the corresponding
    integer value. Returns `logging.WARNING` (30) if input is invalid."""
    if input_level is None:
        return DEFAULT_LOG_LEVEL

    if isinstance(input_level, int) or (isinstance(input_level, str) and input_level.isdigit()):
        log_level = int(input_level)
        if log_level in VALID_LOG_LEVELS:
            return log_level

        logging.warning(
            "Invalid log level (int) in LOG_LEVEL: %s. Falling back to WARNING.", log_level
        )
        return DEFAULT_LOG_LEVEL

    log_level_str = input_level.upper()
    log_level = getattr(logging, log_level_str, None)

    if log_level in VALID_LOG_LEVELS:
        return log_level

    if input_level:
        logging.warning(
            "Invalid log level (str) in LOG_LEVEL: %s. Falling back to WARNING.", input_level
        )

    return DEFAULT_LOG_LEVEL


if LOG_LEVEL_ENV:  # pragma: no cover
    logging.basicConfig(format="%(levelname)s - %(message)s", level=parse_log_level(LOG_LEVEL_ENV))

logger = logging.getLogger(__name__)


__all__ = ["logger", "DEFAULT_LOG_LEVEL", "VALID_LOG_LEVELS"]
