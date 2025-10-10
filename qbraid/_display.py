# Copyright 2025 qBraid
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
