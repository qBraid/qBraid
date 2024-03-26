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
import importlib
import types
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


class LazyLoader(types.ModuleType):
    """Lazily loads a module upon attribute access.

    This class acts as a proxy for a module, loading it only when an attribute
    of the module is accessed for the first time.

    Attributes:
        module_name (str): The full qualified name of the module to be lazily loaded.
        parent_globals (dict): The globals of the parent module, where this loader is used.
        module (module, optional): The loaded module. Initially set to None.

    Args:
        module_name (str): The full qualified name of the module to be lazily loaded.
        parent_globals (dict): The globals of the parent module.
    """

    def __init__(self, module_name, parent_globals):
        super().__init__(module_name)
        self.module_name = module_name
        self.parent_globals = parent_globals
        self.module = None

    def _load(self):
        """Load the module and insert it into the parent's globals."""
        if not self.module:
            # Load the module and insert it into the parent's namespace
            self.module = importlib.import_module(self.module_name)
            self.parent_globals[self.__name__] = self.module

            # Update this object's dict for faster subsequent attribute access
            self.__dict__.update(self.module.__dict__)

        return self.module

    def __getattr__(self, item):
        return getattr(self._load(), item)

    def __dir__(self):
        return dir(self._load)
