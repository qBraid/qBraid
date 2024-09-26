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
Module used for loading entry points and other dynamic imports.

"""
import importlib.metadata
import sys
from typing import Optional, Type

try:
    import pkg_resources
except ImportError:  # pragma: no cover
    pkg_resources = None

from .exceptions import QbraidError


def get_entrypoints(module: str) -> dict[str, object]:
    """
    Retrieves entry points for a given module.

    Args:
        module (str): The name of the module to retrieve entry points for.

    Returns:
        dict[str, object]: Dictionary of entry point names and their associated entry point objects.
    """
    group = f"qbraid.{module}"

    if sys.version_info >= (3, 10):
        entry_points = importlib.metadata.entry_points().select(group=group)
    else:
        entry_points = pkg_resources.iter_entry_points(group=group)

    return {ep.name: ep for ep in entry_points}


def load_entrypoint(module: str, name: str) -> Optional[Type]:
    """
    Load an entrypoint given its module and name.

    Args:
        module (str): Module of entrypoint to load, e.g., "programs"
        name (str): Name of the entrypoint to load within the module.

    Returns:
        Optional[Type]: The loaded entry point class, or None if not found or failed to load.

    Raises:
        ValueError: If the specified entry point cannot be found.
        QbraidError: If the specified entry point fails to load.
    """
    try:
        entry_points = get_entrypoints(module)
        entry_point = entry_points[name]
        return entry_point.load()
    except KeyError as err:
        raise ValueError(f"Entrypoint '{name}' not found in module '{module}'.") from err
    except Exception as err:
        raise QbraidError(f"Failed to load entrypoint '{name}' from module '{module}'.") from err
