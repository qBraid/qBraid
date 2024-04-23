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
Module containing one-step functions for converting between supported
quantum software program types.

.. currentmodule:: qbraid.transpiler.conversions

Submodules
-----------

.. autosummary::
   :toctree: ../stubs/

   braket
   cirq
   openqasm3
   pennylane
   pyquil
   pytket
   qiskit

"""
import importlib
import inspect

# Dynamically import QPROGRAM_LIBS when needed
_qbraid = importlib.import_module("qbraid.programs._import")
_PROGRAM_LIBS = getattr(_qbraid, "_PROGRAM_LIBS", [])
QPROGRAM_LIBS = getattr(_qbraid, "QPROGRAM_LIBS", [])

qprogram_libs_set = set(QPROGRAM_LIBS)

# Cache for storing previously seen valid combinations, including reversed pairs
valid_combinations_cache = set()

# List to store the names of the imported functions
conversion_functions = []

# Base path for the sub-modules
base_path = "qbraid.transpiler.conversions."

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
            p1, p2 = name.split("_to_")
            # Create tuples for both pair and its reverse
            pair = (p1, p2)
            reverse_pair = (p2, p1)

            # Check if either pair or its reverse has been seen as valid before
            if pair in valid_combinations_cache or reverse_pair in valid_combinations_cache:
                globals()[name] = getattr(sub_module, name)
                conversion_functions.append(name)
                continue

            # Check if both p1 and p2 are in the set
            if p1 in qprogram_libs_set and p2 in qprogram_libs_set:
                globals()[name] = getattr(sub_module, name)
                conversion_functions.append(name)
                # Add both the pair and its reverse to the cache
                valid_combinations_cache.add(pair)
                valid_combinations_cache.add(reverse_pair)

    except ModuleNotFoundError:
        pass
