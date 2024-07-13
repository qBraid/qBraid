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
Module containing sub-modules for interfacing with
various quantum software libraries and program types.

.. currentmodule:: qbraid.programs.circuits

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
   qasm
   qiskit

"""
import importlib

from ._model import GateModelProgram


def try_import_module(base_path: str, module_name: str) -> None:
    """Attempt to import a module and append to submodules if successful."""
    try:
        imported_module = importlib.import_module(base_path + module_name)
        submodules.append(module_name)
        globals()[module_name] = imported_module
    except ImportError:
        pass


_qbraid = importlib.import_module("qbraid.programs._import")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})

submodules = []
circuits_module = "qbraid.programs.circuits."
qasm_in_registry = False

for lib in list(NATIVE_REGISTRY.keys()):
    if lib in ["qasm2", "qasm3"]:
        qasm_in_registry = True
        continue

    try_import_module(circuits_module, lib)

if qasm_in_registry:
    try_import_module(circuits_module, "qasm")


__all__ = ["GateModelProgram"]

__all__.extend(submodules)
