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

"""
import importlib

from ._model import GateModelProgram

_qbraid = importlib.import_module("qbraid.programs._import")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})
CIRCUIT_SUBMODULE_CHECKS = NATIVE_REGISTRY.copy()

submodules = []
base_path = "qbraid.programs.gate_model."

key_set = set(CIRCUIT_SUBMODULE_CHECKS.keys())

for lib in key_set:
    try:
        imported_lib = importlib.import_module(base_path + lib)
        submodules.append(lib)
        globals()[lib] = imported_lib

    except ImportError:
        pass


__all__ = ["GateModelProgram"]

__all__.extend(submodules)
