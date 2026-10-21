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
Module containing sub-modules for interfacing with
various quantum software libraries and program types.

.. currentmodule:: qbraid.programs.gate_model

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   GateModelProgram

Submodules
------------

.. autosummary::
   :toctree: ../stubs/

   braket
   cirq
   pennylane
   pyquil
   pytket
   qasm2
   qasm3
   qiskit
   ionq
   cudaq
   aqt_connector

"""
import importlib
import importlib.util

from ._model import GateModelProgram

_qbraid = importlib.import_module("qbraid.programs._import")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})
CIRCUIT_SUBMODULE_CHECKS = NATIVE_REGISTRY.copy()

base_path = "qbraid.programs.gate_model."

# Submodules wrap optional SDKs, so they are imported on first attribute access
# rather than here. find_spec on a child module does not execute it.
submodules = [
    lib for lib in CIRCUIT_SUBMODULE_CHECKS if importlib.util.find_spec(base_path + lib) is not None
]


def __getattr__(name):
    if name in submodules:
        module = importlib.import_module(base_path + name)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["GateModelProgram"]

__all__.extend(submodules)
