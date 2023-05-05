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
Module for utility functions used in displaying data to user

"""
import sys
from typing import Optional


def update_progress_bar(progress: float, status: Optional[str] = None):
    """Internal progress bar function used by :func:`~qbraid.get_devices`
    and :func:`~qbraid.get_jobs`.
    """
    bar_length = 20  # Modify this to change the length of the progress bar
    status = "" if status is None else status
    if progress < 0:
        progress = 0
        status = "Halted\r\n"
    if progress >= 1:
        progress = 1
        status = "Done\r\n"
    block = int(round(bar_length * progress))
    progress_bar = "." * block + " " * (bar_length - block)
    percent = int(progress * 100)
    text = f"\rProgress: [{progress_bar}] {percent}% {status}"
    sys.stdout.write(text)
    sys.stdout.flush()


def running_in_jupyter():
    """
    Determine if running within Jupyter.

    Credit: `braket.ipython_utils <https://github.com/aws/amazon-braket-sdk-python/
    blob/0d28a8fa89263daf5d88bc706e79200d8dc091a8/src/braket/ipython_utils.py>`_.

    Returns:
        bool: True if running in Jupyter, else False.
    """
    in_ipython = False
    in_ipython_kernel = False

    # if IPython hasn't been imported, there's nothing to check
    if "IPython" in sys.modules:
        get_ipython = sys.modules["IPython"].__dict__["get_ipython"]

        ip = get_ipython()
        in_ipython = ip is not None

    if in_ipython:
        in_ipython_kernel = getattr(ip, "kernel", None) is not None

    return in_ipython_kernel
