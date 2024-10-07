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
Module defining PyQuboModel Class

"""
from __future__ import annotations

from pyqubo import Model

from qbraid.programs.exceptions import ProgramTypeError

from ._model import AnnealingProgram, QuboProblem


class PyQuboModel(AnnealingProgram):
    """AnnealingProblem subclass that accepts a cpp_pyqubo.Model."""

    def __init__(self, program: Model):
        super().__init__(program)
        if not isinstance(program, Model):
            raise ProgramTypeError(
                message=f"Expected 'pyqubo.Model' object, got '{type(program)}'."
            )

    def to_problem(self) -> QuboProblem:
        """Converts the cpp_pyqubo.Model to a Problem instance."""
        qubo, offset = self.program.to_qubo()
        coefficients = {}

        for key, value in qubo.items():
            coefficients[key] = value

        return QuboProblem(coefficients, offset)
