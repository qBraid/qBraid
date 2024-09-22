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
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    about
    clear_cache
    cache_disabled

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError

"""
from ._about import about
from ._caching import cache_disabled, clear_cache
from ._version import __version__
from .exceptions import QbraidError

__all__ = [
    "about",
    "QbraidError",
    "__version__",
    "clear_cache",
    "cache_disabled",
]

_lazy_mods = ["interface", "passes", "programs", "runtime", "transpiler", "visualization"]

_lazy_objs = {
    "interface": [
        "circuits_allclose",
        "random_circuit",
    ],
    "programs": [
        "AnalogHamiltonianProgram",
        "GateModelProgram",
        "ProgramSpec",
        "Qasm2String",
        "Qasm3String",
        "QuantumProgram",
        "QPROGRAM",
        "QPROGRAM_NATIVE",
        "QPROGRAM_REGISTRY",
        "NATIVE_REGISTRY",
        "get_program_type_alias",
        "load_program",
        "register_program_type",
        "unregister_program_type",
    ],
    "transpiler": [
        "Conversion",
        "ConversionGraph",
        "ConversionScheme",
        "transpile",
    ],
    "runtime": [
        "AhsResultData",
        "AhsShotResult",
        "GateModelResultData",
        "QuantumDevice",
        "QuantumJob",
        "QuantumProvider",
        "Result",
        "ResultData",
        "RuntimeOptions",
        "TargetProfile",
    ],
}


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module

    for mod_name, objects in _lazy_objs.items():
        if name in objects:
            import importlib  # pylint: disable=import-outside-toplevel

            module = importlib.import_module(f".{mod_name}", __name__)
            obj = getattr(module, name)
            globals()[name] = obj
            return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        __all__ + _lazy_mods + [item for sublist in _lazy_objs.values() for item in sublist]
    )
