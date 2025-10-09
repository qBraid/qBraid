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
Module defining QuantumProgram Class

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

from qbraid._logging import logger

from .alias_manager import get_program_type_alias
from .exceptions import ProgramTypeError
from .experiment import ExperimentType
from .registry import QPROGRAM_REGISTRY
from .spec import ProgramSpec

if TYPE_CHECKING:
    import qbraid.programs
    import qbraid.runtime


class QuantumProgram(ABC):
    """Abstract class for qbraid program wrapper objects."""

    def __init__(self, program: qbraid.programs.QPROGRAM):
        self.spec = self.get_spec(program)
        self._program: Any = None
        self.program = program

    @property
    def program(self) -> qbraid.programs.QPROGRAM:
        """Return the quantum program."""
        return self._program

    @program.setter
    def program(self, value: qbraid.programs.QPROGRAM) -> None:
        """Set the quantum program."""
        expected_type = QPROGRAM_REGISTRY.get(self.spec.alias)
        if not isinstance(value, expected_type):
            raise ProgramTypeError(
                message=(
                    f"Expected program type of '{expected_type}' for "
                    f"derived type alias '{self.spec.alias}'."
                )
            )
        self._program = value

    @property
    def experiment_type(self) -> Optional[ExperimentType]:
        """Returns the ExperimentType corresponding to the sub-module of the program."""
        return self.spec.experiment_type

    @staticmethod
    def get_spec(program: Any) -> ProgramSpec:
        """Return the program spec."""
        try:
            alias = get_program_type_alias(program)
        except ProgramTypeError as err:
            logger.info(err)
            alias = None

        return ProgramSpec(type(program), alias)

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        """Total count of qubits needed by a quantum device
        to execute this program."""

    @abstractmethod
    def transform(self, device: qbraid.runtime.QuantumDevice) -> None:
        """Transform program to according to device target profile."""

    @abstractmethod
    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
