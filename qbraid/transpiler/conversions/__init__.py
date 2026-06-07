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
Module containing one-step functions for converting between supported
quantum software program types.

.. currentmodule:: qbraid.transpiler.conversions

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
   cudaq

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


def _update_registered_conversions() -> None:
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


_update_registered_conversions()
