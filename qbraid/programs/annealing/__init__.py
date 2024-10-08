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

.. currentmodule:: qbraid.programs.annealing

Classes
--------

.. autosummary::
   :toctree: ../stubs/
    
    ProblemType
    Problem
    AnnealingProgram
    QuboProblem
    ProblemEncoder

Submodules
------------

.. autosummary::
   :toctree: ../stubs/

    cpp_pyqubo

"""
import importlib

from ._model import AnnealingProgram, Problem, ProblemEncoder, ProblemType, QuboProblem

_qbraid = importlib.import_module("qbraid.programs._import")
NATIVE_REGISTRY = getattr(_qbraid, "NATIVE_REGISTRY", {})

submodules = []
base_path = "qbraid.programs.annealing."

for lib in NATIVE_REGISTRY:
    try:
        imported_lib = importlib.import_module(base_path + lib)
        submodules.append(lib)
        globals()[lib] = imported_lib

    except ImportError:
        pass


__all__ = ["ProblemType", "Problem", "AnnealingProgram", "QuboProblem", "ProblemEncoder"]

__all__.extend(submodules)
