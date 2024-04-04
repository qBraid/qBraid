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
import os
import sys
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
    """Lazily import a module, mainly to avoid pulling in large dependencies.

    This class acts as a proxy for a module, loading it only when an attribute
    of the module is accessed for the first time.

    Args:
        local_name: The local name that the module will be refered to as.
        parent_module_globals: The globals of the module where this should be imported.
            Typically this will be globals().
        name: The full qualified name of the module.
    """

    def __init__(self, local_name, parent_module_globals, name):
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals
        self._module = None
        self._docs_build = self._is_sphinx_build()
        super().__init__(name)

    def _is_sphinx_build(self):
        """Check if the current environment is a Sphinx build."""
        return os.environ.get("SPHINX_BUILD") == "1" or "sphinx" in sys.modules

    def _load(self):
        """Load the module and insert it into the parent's globals."""
        if self._module is None:
            self._module = importlib.import_module(self.__name__)
            self._parent_module_globals[self._local_name] = self._module
            self.__dict__.update(self._module.__dict__)
        return self._module

    def __getattr__(self, item):
        if self._docs_build:
            self._load()  # Ensure module is loaded when Sphinx is running
        module = self._load()
        return getattr(module, item)

    def __dir__(self):
        if self._docs_build:
            self._load()  # Ensure module is loaded when Sphinx is running
        module = self._load()
        return dir(module)
