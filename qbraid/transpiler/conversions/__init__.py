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
Module containing one-step functions for converting between supported
quantum software program types.

.. currentmodule:: qbraid.transpiler.conversions

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   update_registered_conversions


Submodules
-----------

.. autosummary::
   :toctree: ../stubs/
   
   braket_ahs
   braket
   cirq
   openqasm3
   qasm2
   qasm3
   pennylane
   pyquil
   pytket
   qiskit

"""
import importlib
import inspect

# Dynamically import QPROGRAM_ALIASES when needed
_qbraid = importlib.import_module("qbraid.programs._import")
_registry = importlib.import_module("qbraid.programs.registry")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})
QPROGRAM_REGISTRY = getattr(_registry, "QPROGRAM_REGISTRY", {})

# Cache for storing previously seen valid combinations, including reversed pairs
valid_combinations_cache = set()

conversion_functions = []


def update_registered_conversions() -> None:
    """
    Dynamically update the list of conversion functions based on current
    NATIVE_REGISTRY and QPROGRAM_REGISTRY. Adds valid conversion functions
    to the global namespace and maintains a cache of seen valid combinations.
    """
    conversion_functions.clear()

    # Base path for the sub-modules
    base_path = "qbraid.transpiler.conversions."

    for lib in NATIVE_REGISTRY:
        try:
            # Dynamically import the sub-module
            sub_module = importlib.import_module(base_path + lib)

            # Extract function names from the sub-module
            function_names = [
                name
                for name in dir(sub_module)
                if callable(getattr(sub_module, name))
                and inspect.isfunction(getattr(sub_module, name))
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
                if (p1 in NATIVE_REGISTRY or p2 in NATIVE_REGISTRY) and (
                    p1 in QPROGRAM_REGISTRY and p2 in QPROGRAM_REGISTRY
                ):
                    globals()[name] = getattr(sub_module, name)
                    conversion_functions.append(name)
                    # Add both the pair and its reverse to the cache
                    valid_combinations_cache.add(pair)
                    valid_combinations_cache.add(reverse_pair)

        except ModuleNotFoundError:
            pass


update_registered_conversions()
