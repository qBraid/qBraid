# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
==============================================
Transpiler  (:mod:`qbraid.transpiler`)
==============================================

.. currentmodule:: qbraid.transpiler

.. autosummary::
   :toctree: ../stubs/

   CircuitConversionError

"""
import importlib
import inspect

from qbraid.transpiler.exceptions import CircuitConversionError

# Dynamically import QPROGRAM_LIBS when needed
_qbraid = importlib.import_module("qbraid._qprogram")
_PROGRAM_LIBS = getattr(_qbraid, "_PROGRAM_LIBS", [])

# List to store the names of the imported functions
conversion_functions = []

# Base path for the sub-modules
base_path = "qbraid.transpiler."

# Iterate over the installed libraries
for lib in _PROGRAM_LIBS:
    try:
        # Dynamically import the sub-module
        sub_module = importlib.import_module(base_path + lib)

        # Extract function names from the sub-module
        function_names = [
            name
            for name in dir(sub_module)
            if callable(getattr(sub_module, name)) and inspect.isfunction(getattr(sub_module, name))
        ]

        # Add functions to the current namespace
        for name in function_names:
            globals()[name] = getattr(sub_module, name)
            conversion_functions.append(name)

    except ModuleNotFoundError:
        pass
