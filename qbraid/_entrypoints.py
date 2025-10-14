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
Module used for loading entry points and other dynamic imports.

"""
import importlib.metadata
from typing import Optional, Type

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

    entry_points = importlib.metadata.entry_points().select(group=group)

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
