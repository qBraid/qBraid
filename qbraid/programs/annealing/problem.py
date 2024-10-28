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
Module defining qBraid runtime schemas.
"""
from __future__ import annotations

from qbraid.programs.exceptions import ProgramTypeError

from ._model import AnnealingProgram, Problem


class QuboProgram(AnnealingProgram):
    """Class representing a QUBO problem."""

    def __init__(self, program: Problem):
        super().__init__(program)
        self.program = program
        if not isinstance(program, Problem):
            raise ProgramTypeError(
                message=f"Expected 'pyqubo.Model' object, got '{type(program)}'."
            )

    def to_problem(self) -> Problem:
        """Return the QUBO problem."""
        return self.program
