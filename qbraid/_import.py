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
Module used for lazy loading of submodules.

"""
from typing import Optional, Type

import pkg_resources

from .exceptions import QbraidError


def _load_entrypoint(module: str, name: str) -> Optional[Type]:
    """Load an entrypoint given its category and name, optionally with a vendor.

    Args:
        module (str): Module of entrypoint to load, e.g., "programs" or "providers".
        name (str): Name of the entrypoint to load within the module.

    Returns:
        Optional[Type]: The loaded entry point class, or None if not found or failed to load.

    Raises:
        ValueError: If the specified entry point cannot be found.
        QbraidError: If the specifiedentry point fails to load.
    """
    group = f"qbraid.{module}"
    try:
        entrypoints = {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}
        entry_point = entrypoints[name]
        return entry_point.load()
    except KeyError as err:
        raise ValueError(f"Entrypoint '{name}' not found in module '{module}'.") from err
    except Exception as err:
        raise QbraidError(f"Failed to load entrypoint '{name}' from module '{module}'.") from err
