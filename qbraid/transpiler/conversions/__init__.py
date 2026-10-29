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
   qrisp

"""
import importlib
import inspect
from pathlib import Path

from qbraid._logging import logger

# Dynamically import QPROGRAM_ALIASES when needed
_qbraid = importlib.import_module("qbraid.programs._import")
_registry = importlib.import_module("qbraid.programs.registry")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})
QPROGRAM_REGISTRY = getattr(_registry, "QPROGRAM_REGISTRY", {})

# Cache for storing previously seen valid combinations, including reversed pairs
valid_combinations_cache = set()

conversion_functions = []

_QBRAID_ROOT = Path(__file__).resolve().parents[2]


def _raised_in_qbraid(err: BaseException) -> bool:
    """Whether the innermost frame of ``err``, ignoring frozen importlib frames, is in qbraid."""
    # Walked by hand: traceback.extract_tb obeys sys.tracebacklimit, which some packages set.
    filename = None
    tb = err.__traceback__
    while tb is not None:
        if not tb.tb_frame.f_code.co_filename.startswith("<"):
            filename = tb.tb_frame.f_code.co_filename
        tb = tb.tb_next
    return filename is not None and Path(filename).resolve().is_relative_to(_QBRAID_ROOT)


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

        except Exception as err:  # pylint: disable=broad-exception-caught
            in_qbraid = _raised_in_qbraid(err)
            missing = err.name if isinstance(err, ModuleNotFoundError) else None
            if missing == base_path + lib:
                continue
            # qbraid importing an optional SDK that isn't installed is expected. A missing
            # qbraid module is not, nor is any other error raised from qbraid's own code
            # while lib's SDK loads. Failures raised inside an SDK, lib's own or another
            # one its conversions import, mean a broken install and are skipped.
            if missing and in_qbraid and missing.split(".")[0] != "qbraid":
                continue
            if in_qbraid and NATIVE_REGISTRY.get(lib) is not None:
                raise
            logger.warning("Skipping conversions for '%s': %s: %s", lib, type(err).__name__, err)


_update_registered_conversions()
