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

    def to_problem(self, **kwargs) -> QuboProblem:
        """Converts the cpp_pyqubo.Model to a Problem instance."""
        qubo, _ = self.program.to_qubo(**kwargs)
        coefficients = {}

        for key, value in qubo.items():
            coefficients[key] = value

        return QuboProblem(coefficients)
