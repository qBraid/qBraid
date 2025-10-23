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
