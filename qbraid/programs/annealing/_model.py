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
Module defining AnnealingProblem Class

"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from qbraid.programs.program import QuantumProgram

if TYPE_CHECKING:
    import qbraid.runtime


class ProblemType(Enum):
    """Enumeration for different types of annealing models.

    Attributes:
        QUBO: Quadratic Unconstrained Binary Optimization model with binary variables.
        ISING: Ising model with spin variables (-1 or +1).
    """

    QUBO = "qubo"
    ISING = "ising"


@dataclass
class Problem:
    """Represents an annealing problem, including linear and quadratic terms.

    Attributes:
        problem_type: An instance of ProblemType indicating whether the model is QUBO or ISING.
        linear: A dictionary representing the linear coefficients.
        quadratic: A dictionary representing the quadratic coefficients.
        offset: A float representing the constant offset.

    """

    problem_type: ProblemType
    linear: dict[str, float] = field(default_factory=dict)
    quadratic: dict[tuple[str, str], float] = field(default_factory=dict)
    offset: float = 0.0

    def num_variables(self) -> int:
        """Return the number of variables in the problem."""
        variables = set(self.linear.keys())
        for key in self.quadratic:
            variables.update(key)
        return len(variables)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Problem):
            return False
        if self.offset != other.offset or self.problem_type != other.problem_type:
            return False
        if self.linear != other.linear or len(self.quadratic) != len(other.quadratic):
            return False
        for key, value in self.quadratic.items():
            if key in other.quadratic:
                if other.quadratic[key] != value:
                    return False
            elif (key[1], key[0]) in other.quadratic:
                if other.quadratic[(key[1], key[0])] != value:
                    return False
            else:
                return False
        return True


@dataclass
class QuboProblem(Problem):
    """Represents a QUBO problem, subclass of Problem that only includes quadratic coefficients."""

    def __init__(self, coefficients: dict[tuple[str, str], float], offset: float = 0.0):
        super().__init__(
            problem_type=ProblemType.QUBO,
            linear={},
            quadratic=coefficients,
            offset=offset,
        )


class AnnealingProgram(QuantumProgram, ABC):
    """Abstract class for annealing problems."""

    @property
    def num_qubits(self) -> int:
        """Number of qubits needed by a quantum device to execute this program."""
        return self.to_problem().num_variables()

    def transform(self, device: qbraid.runtime.QuantumDevice) -> None:
        """Transform program according to device target profile."""
        raise NotImplementedError

    @abstractmethod
    def to_problem(self) -> Problem:
        """Return a Problem data class representing this annealing problem."""

    def to_json(self) -> str:
        """Serialize the annealing problem to a JSON string."""
        return json.dumps(self, cls=ProblemEncoder)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.to_problem() == other.to_problem()


class ProblemEncoder(json.JSONEncoder):
    """Custom JSON encoder for Problem data class."""

    def default(self, o: Any) -> Any:
        if isinstance(o, AnnealingProgram):
            return self.default(o.to_problem())
        if isinstance(o, Problem):
            data = {
                "offset": o.offset,
                "problem_type": o.problem_type.value,
            }
            if o.linear:
                data["linear"] = o.linear
            if o.quadratic:
                quadratic_json = {json.dumps(key): value for key, value in o.quadratic.items()}
                data["quadratic"] = quadratic_json
            return data
        if isinstance(o, ProblemType):
            return o.value

        return super().default(o)  # pragma: no cover
