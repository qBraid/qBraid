# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
