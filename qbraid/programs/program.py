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
