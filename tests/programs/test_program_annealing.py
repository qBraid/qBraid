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
Unit tests for qbraid.programs.annealing module.

"""
import json

import pytest

try:
    from pyqubo import Spin

    from qbraid.programs import ProgramTypeError, unregister_program_type
    from qbraid.programs.annealing import (
        AnnealingProgram,
        Problem,
        ProblemEncoder,
        ProblemType,
        QuboProblem,
    )
    from qbraid.programs.annealing.cpp_pyqubo import PyQuboModel

    pyqubo_not_installed = False
except ImportError:
    pyqubo_not_installed = True


pytestmark = pytest.mark.skipif(pyqubo_not_installed, reason="pyqubo not installed")


@pytest.fixture
def pyqubo_model():
    """Creates and returns a compiled pyqubo model using Spin variables."""
    s1, s2, s3, s4 = Spin("s1"), Spin("s2"), Spin("s3"), Spin("s4")
    H = (4 * s1 + 2 * s2 + 7 * s3 + s4) ** 2
    model = H.compile()
    return model


@pytest.fixture
def mock_annealing_program():
    """Creates and returns a dummy subclass of AnnealingProgram for testing."""

    class MockAnnealingProgram(AnnealingProgram):
        """A dummy subclass of AnnealingProgram for testing."""

        # pylint: disable-next=super-init-not-called
        def __init__(self, problem: Problem):
            self._problem = problem

        def to_problem(self) -> Problem:
            return self._problem

    return MockAnnealingProgram


def test_problem_initialization():
    """Tests the initialization of a Problem instance with specified
    linear and quadratic coefficients."""
    problem = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0, "x2": -1.5},
        quadratic={("x1", "x2"): 0.5},
        offset=2.0,
    )

    assert problem.problem_type == ProblemType.QUBO
    assert problem.linear == {"x1": 1.0, "x2": -1.5}
    assert problem.quadratic == {("x1", "x2"): 0.5}
    assert problem.offset == 2.0
    assert problem.num_variables() == 2


def test_problem_equality():
    """Tests the equality comparison between two Problem instances with
    identical properties."""
    problem1 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0},
        quadratic={("x1", "x2"): 0.5},
        offset=2.0,
    )
    problem2 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0},
        quadratic={("x2", "x1"): 0.5},
        offset=2.0,
    )

    assert problem1 == problem2


def test_qubo_problem_initialization():
    """Tests the initialization of a QuboProblem instance with given
    quadratic coefficients and offset."""
    coefficients = {("x1", "x2"): 0.5, ("x2", "x3"): -1.0}
    qubo_problem = QuboProblem(coefficients, offset=1.0)

    assert qubo_problem.problem_type == ProblemType.QUBO
    assert qubo_problem.quadratic == coefficients
    assert qubo_problem.offset == 1.0
    assert qubo_problem.num_variables() == 3


def test_pyqubo_model_initialization(pyqubo_model):
    """Tests the initialization of a PyQuboModel instance using a pyqubo model fixture."""
    pyqubo_model_instance = PyQuboModel(pyqubo_model)

    assert pyqubo_model_instance.program == pyqubo_model


def test_pyqubo_model_invalid_initialization():
    """Tests that initializing a PyQuboModel with an invalid input raises a ProgramTypeError."""
    try:
        with pytest.raises(ProgramTypeError):
            PyQuboModel(("invalid", "program"))
    finally:
        unregister_program_type("tuple")


def test_pyqubo_model_to_problem(pyqubo_model):
    """Tests the conversion of a PyQuboModel instance to a QuboProblem."""
    pyqubo_model_instance = PyQuboModel(pyqubo_model)

    problem = pyqubo_model_instance.to_problem()
    assert isinstance(problem, QuboProblem)
    assert problem.num_variables() == 4


def test_problem_encoder(mock_annealing_program):
    """Tests the ProblemEncoder class for encoding Problem instances to JSON."""
    problem = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0, "x2": -1.5},
        quadratic={("x1", "x2"): 0.5},
        offset=2.0,
    )

    problem_json = json.dumps(problem, cls=ProblemEncoder)
    expected_problem_json = json.dumps(
        {
            "offset": 2.0,
            "problem_type": "qubo",
            "linear": {"x1": 1.0, "x2": -1.5},
            "quadratic": {'["x1", "x2"]': 0.5},
        }
    )
    assert problem_json == expected_problem_json

    mock_program = mock_annealing_program(problem)

    program_json = json.dumps(mock_program, cls=ProblemEncoder)
    assert program_json == expected_problem_json == mock_program.to_json()

    problem_type_json = json.dumps(ProblemType.QUBO, cls=ProblemEncoder)
    assert problem_type_json == '"qubo"'
