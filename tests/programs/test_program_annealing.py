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
from unittest.mock import Mock

import pytest

try:
    from pyqubo import Spin

    from qbraid.programs import ExperimentType, ProgramTypeError, unregister_program_type
    from qbraid.programs.annealing import (
        AnnealingProgram,
        Problem,
        ProblemEncoder,
        ProblemType,
        QuboProblem,
    )
    from qbraid.programs.annealing.cpp_pyqubo import PyQuboModel
    from qbraid.programs.annealing.qubo import QuboProgram
    from qbraid.runtime.native.provider import _serialize_program

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
    )

    assert problem.problem_type == ProblemType.QUBO
    assert problem.linear == {"x1": 1.0, "x2": -1.5}
    assert problem.quadratic == {("x1", "x2"): 0.5}
    assert problem.num_variables() == 2


def test_problem_equality():
    """Tests the equality comparison between two Problem instances with
    identical properties."""
    problem1 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0},
        quadratic={("x1", "x2"): 0.5},
    )
    problem2 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0},
        quadratic={("x2", "x1"): 0.5},
    )

    assert problem1 == problem2


def test_qubo_problem_initialization():
    """Tests the initialization of a QuboProblem instance with given
    quadratic coefficients and offset."""
    coefficients = {("x1", "x2"): 0.5, ("x2", "x3"): -1.0}
    qubo_problem = QuboProblem(coefficients)

    assert qubo_problem.problem_type == ProblemType.QUBO
    assert qubo_problem.quadratic == coefficients
    assert qubo_problem.num_variables() == 3


def test_pyqubo_model_initialization(pyqubo_model):
    """Tests the initialization of a PyQuboModel instance using a pyqubo model fixture."""
    pyqubo_model_instance = PyQuboModel(pyqubo_model)

    assert pyqubo_model_instance.program == pyqubo_model


def get_program_classes():
    """Dynamically import and return program classes for testing."""
    try:
        return [PyQuboModel, QuboProgram]
    except NameError:
        return []


@pytest.mark.parametrize("program_class", get_program_classes())
def test_invalid_program_initialization(program_class):
    """Tests that initializing a program with an invalid input raises a ProgramTypeError."""
    try:
        with pytest.raises(ProgramTypeError):
            program_class(("invalid", "program"))
    finally:
        unregister_program_type("tuple")


def test_pyqubo_model_to_problem(pyqubo_model):
    """Tests the conversion of a PyQuboModel instance to a QuboProblem."""
    pyqubo_model_instance = PyQuboModel(pyqubo_model)

    problem = pyqubo_model_instance.to_problem()
    assert isinstance(problem, QuboProblem)
    assert problem.num_variables() == 4
    assert pyqubo_model_instance.num_qubits == 4


def test_problem_encoder(mock_annealing_program):
    """Tests the ProblemEncoder class for encoding Problem instances to JSON."""
    problem = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0, "x2": -1.5},
        quadratic={("x1", "x2"): 0.5},
    )

    problem_json = json.dumps(problem, cls=ProblemEncoder)
    expected_problem_json = json.dumps(
        {
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


def test_problem_eq_different_type():
    """Test __eq__ returns False when compared with a non-Problem instance."""
    problem = Problem(problem_type=ProblemType.QUBO)
    assert problem != "Not a Problem instance"


def test_problem_eq_different_problem_type():
    """Test __eq__ returns False when problem_types are different."""
    problem1 = Problem(problem_type=ProblemType.QUBO)
    problem2 = Problem(problem_type=ProblemType.ISING)
    assert problem1 != problem2


def test_problem_eq_different_linear():
    """Test __eq__ returns False when linear terms are different."""
    problem1 = Problem(problem_type=ProblemType.QUBO, linear={"x1": 1.0})
    problem2 = Problem(problem_type=ProblemType.QUBO, linear={"x1": 2.0})
    assert problem1 != problem2


def test_problem_eq_different_quadratic_length():
    """Test __eq__ returns False when quadratic term lengths are different."""
    problem1 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 0.5})
    problem2 = Problem(problem_type=ProblemType.QUBO, quadratic={})
    assert problem1 != problem2


def test_problem_eq_quadratic_key_not_in_other():
    """Test __eq__ returns False when a quadratic key is missing in the other problem."""
    problem1 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 0.5})
    problem2 = Problem(problem_type=ProblemType.QUBO, quadratic={("x2", "x3"): 0.5})
    assert problem1 != problem2


def test_problem_eq_quadratic_value_differs():
    """Test __eq__ returns False when quadratic values differ for the same key."""
    problem1 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 0.5})
    problem2 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 1.0})
    assert problem1 != problem2


def test_problem_eq_quadratic_keys_swapped_same_value():
    """Test __eq__ returns True when quadratic keys are swapped but values are the same."""
    problem1 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 0.5})
    problem2 = Problem(problem_type=ProblemType.QUBO, quadratic={("x2", "x1"): 0.5})
    assert problem1 == problem2


def test_problem_eq_quadratic_keys_swapped_value_differs():
    """Test __eq__ returns False when quadratic keys are swapped and values differ."""
    problem1 = Problem(problem_type=ProblemType.QUBO, quadratic={("x1", "x2"): 0.5})
    problem2 = Problem(problem_type=ProblemType.QUBO, quadratic={("x2", "x1"): 1.0})
    assert problem1 != problem2


def test_problem_eq_all_attributes_same():
    """Test __eq__ returns True when all attributes are identical."""
    problem1 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0, "x2": -1.5},
        quadratic={("x1", "x2"): 0.5, ("x3", "x4"): -0.3},
    )
    problem2 = Problem(
        problem_type=ProblemType.QUBO,
        linear={"x1": 1.0, "x2": -1.5},
        quadratic={("x4", "x3"): -0.3, ("x2", "x1"): 0.5},
    )
    assert problem1 == problem2


def test_annealing_program_eq(mock_annealing_program):
    """Test __eq__ returns True when compared with an equivalent instance."""
    problem = Problem(problem_type=ProblemType.QUBO)
    annealing_program = mock_annealing_program(problem)
    annealing_program_2 = mock_annealing_program(problem)
    assert annealing_program == annealing_program_2


def test_annealing_program_eq_different_type(mock_annealing_program):
    """Test __eq__ returns False when compared with a non-AnnealingProgram instance."""
    problem = Problem(problem_type=ProblemType.QUBO)
    annealing_program = mock_annealing_program(problem)
    assert annealing_program != "Not an AnnealingProgram instance"


def test_runtime_serliaze_qubo(pyqubo_model):
    """Test that the _pyqubo_to_json function returns the expected JSON string."""
    pyqubo_json = _serialize_program(pyqubo_model)
    pyqubo_dict = {"problem": json.loads(pyqubo_json["problem"])}

    expected_dict = {
        "problem": {
            "problem_type": "qubo",
            "quadratic": {
                '["s1", "s1"]': -160.0,
                '["s4", "s2"]': 16.0,
                '["s3", "s1"]': 224.0,
                '["s2", "s2"]': -96.0,
                '["s4", "s1"]': 32.0,
                '["s1", "s2"]': 64.0,
                '["s3", "s2"]': 112.0,
                '["s3", "s3"]': -196.0,
                '["s4", "s4"]': -52.0,
                '["s4", "s3"]': 56.0,
            },
        }
    }

    assert pyqubo_dict == expected_dict


def test_problem_encoder_super_default():
    """Test that the ProblemEncoder falls back to the default encoder."""
    data = {"data": "test_data"}
    encoded_obj = json.dumps(data, cls=ProblemEncoder)
    expected_output = '{"data": "test_data"}'
    assert encoded_obj == expected_output


def test_get_pyqubo_experiment_type(pyqubo_model):
    """Test that the PyQuboModel correctly identifies the experiment type as ANNEALING."""
    program = PyQuboModel(pyqubo_model)
    assert program.experiment_type == ExperimentType.ANNEALING


def test_pyqubo_model_transform(pyqubo_model):
    """Test that the PyQuboModel transform method does not modify the program."""
    program = PyQuboModel(pyqubo_model)
    program.transform(device=Mock())
    assert program.program == pyqubo_model
