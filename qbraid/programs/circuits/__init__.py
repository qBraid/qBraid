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

"""
import importlib
import sys
import warnings

from qbraid.programs.gate_model._model import GateModelProgram as GateModelProgram

warnings.warn(
    "The 'qbraid.programs.circuits' module has been renamed to "
    "'qbraid.programs.gate_model'. Please update your imports. "
    "This backward compatibility layer will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

# Redirect imports from 'circuits' to 'gate_model'
module_name = sys.modules[__name__]

submodules = [
    "_model",
    "braket",
    "cirq",
    "ionq",
    "pennylane",
    "pyquil",
    "pytket",
    "qasm2",
    "qasm3",
    "qiskit",
]

# Dynamically import and register submodules
for submodule in submodules:
    new_module_name = f"qbraid.programs.gate_model.{submodule}"
    sys.modules[f"{__name__}.{submodule}"] = importlib.import_module(new_module_name)
