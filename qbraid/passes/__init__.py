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
Module for runtime quantum program transformations.

.. currentmodule:: qbraid.passes

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/
   
   CompilationError
   QasmDecompositionError

"""
from .exceptions import CompilationError, QasmDecompositionError

__all__ = ["CompilationError", "QasmDecompositionError"]

_lazy_mods = ["qasm"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)
