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
Module providing unified conversions interface between supported
quantum program types.

.. currentmodule:: qbraid.transpiler

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   Conversion
   ConversionGraph
   ConversionScheme

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   transpile
   requires_extras

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   CircuitConversionError
   NodeNotFoundError
   ConversionPathNotFoundError

"""
from .annotations import requires_extras
from .converter import transpile
from .edge import Conversion
from .exceptions import CircuitConversionError, ConversionPathNotFoundError, NodeNotFoundError
from .graph import ConversionGraph
from .scheme import ConversionScheme

__all__ = [
    "requires_extras",
    "transpile",
    "Conversion",
    "ConversionGraph",
    "ConversionScheme",
    "CircuitConversionError",
    "NodeNotFoundError",
    "ConversionPathNotFoundError",
]

_lazy_mods = ["conversions"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)
