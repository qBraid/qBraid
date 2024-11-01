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
Module defining QuboProgram Class

"""
from __future__ import annotations

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import QuboCoefficientsDict

from ._model import AnnealingProgram, QuboProblem


class QuboProgram(AnnealingProgram):
    """AnnealingProblem subclass that accepts a qbraid.typer.QuboCoefficientsDict."""

    def __init__(self, program: QuboCoefficientsDict):
        super().__init__(program)
        if not isinstance(program, QuboCoefficientsDict):
            raise ProgramTypeError(
                message=f"Expected '{QuboCoefficientsDict}' object, got '{type(program)}'."
            )

    def to_problem(self) -> QuboProblem:
        """Converts the QuboCoefficientsDict a Problem instance."""
        return QuboProblem(self.program)
