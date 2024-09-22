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
Configures display options based on environment context.

"""
import sys

from ._logging import logger


def running_in_jupyter() -> bool:
    """
    Determine if running within Jupyter.

    Returns:
        bool: True if running in Jupyter, else False.
    """
    try:
        if "IPython" in sys.modules:
            get_ipython = sys.modules["IPython"].__dict__["get_ipython"]
            ip = get_ipython()
            if ip is not None:
                return getattr(ip, "kernel", None) is not None
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Error checking if running in Jupyter: %s", err)

    return False
