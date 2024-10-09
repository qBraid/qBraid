# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for TargetProfile class

"""
import pytest
from pydantic import ValidationError

from qbraid.programs import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.profile import TargetProfile


@pytest.fixture
def valid_program_spec() -> ProgramSpec:
    """Fixture to provide a valid ProgramSpec instance."""
    return ProgramSpec(program_type=str, alias="qasm2")


def create_target_profile(experiment_type, basis_gates, program_spec):
    """Helper function to create a TargetProfile with given parameters."""
    return TargetProfile(
        device_id="device123",
        simulator=True,
        experiment_type=experiment_type,
        num_qubits=5,
        program_spec=program_spec,
        provider_name="Heisenberg",
        basis_gates=basis_gates,
    )


@pytest.fixture
def target_profile_openqasm(valid_program_spec) -> TargetProfile:
    """Fixture to provide a valid TargetProfile instance with OPENQASM action type."""
    return create_target_profile(
        experiment_type=ExperimentType.GATE_MODEL,
        basis_gates=["ms", "gpi", "gpi2"],
        program_spec=valid_program_spec,
    )


@pytest.fixture
def target_profile_ahs(valid_program_spec) -> list[TargetProfile]:
    """Fixture to provide a valid TargetProfile instance with AHS action type."""
    return create_target_profile(
        experiment_type=ExperimentType.AHS, basis_gates=None, program_spec=valid_program_spec
    )


@pytest.mark.parametrize(
    "simulator, local",
    [
        (True, False),  # simulator
        (False, False),  # QPU
        (True, True),  # local simulator
    ],
)
def test_target_profile_simulator_and_local_fields(simulator, local, valid_program_spec):
    """Ensure that the constructor correctly populates simulator and local fields."""
    profile = TargetProfile(
        device_id="device123",
        simulator=simulator,
        local=local,
        num_qubits=5,
        program_spec=valid_program_spec,
    )
    assert profile.simulator == simulator
    assert profile.get("local") == local


def test_target_profile_raise_for_bad_input():
    """
    Test that the TargetProfile constructor raises appropriate TypeError
    or ValueError for invalid inputs.
    """
    with pytest.raises(ValidationError):
        TargetProfile(device_id=123, simulator=True)
    with pytest.raises(ValidationError):
        TargetProfile(device_id="device123", simulator="invalid_type")
    with pytest.raises(ValidationError):
        TargetProfile(device_id="device123", simulator=True, experiment_type="invalid_action")
    with pytest.raises(ValidationError):
        TargetProfile(device_id="device123", simulator=True, num_qubits="five")
    with pytest.raises(ValidationError):
        TargetProfile(device_id="device123", simulator=True, program_spec="not_a_spec")
    with pytest.raises(ValidationError):
        TargetProfile(device_id="device123", simulator=True, provider_name=10)
    with pytest.raises(ValidationError):
        TargetProfile(device_id="1234", simulator=True, basis_gates=123)
    with pytest.raises(ValidationError):
        TargetProfile(device_id="1234", simulator=True, basis_gates=[1, 2, 3])
    with pytest.raises(ValidationError):
        TargetProfile(device_id="1234", simulator=True, basis_gates=[1, "cx", "h"])
    with pytest.raises(ValidationError):
        TargetProfile(
            device_id="device123",
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            basis_gates=99,
        )
    with pytest.raises(ValidationError):
        TargetProfile(
            device_id="device123",
            simulator=True,
            experiment_type=ExperimentType.GATE_MODEL,
            basis_gates=[None],
        )
    with pytest.raises(ValidationError):
        TargetProfile(
            device_id="device123",
            simulator=True,
            basis_gates=["ms", "gpi", "gpi2"],
        )


def test_target_profile_openqasm_len(target_profile_openqasm):
    """Test the __len__ method of TargetProfile"""
    assert len(target_profile_openqasm) == 7


def test_target_profile_ahs_len(target_profile_ahs):
    """Test the __len__ method of TargetProfile"""
    assert len(target_profile_ahs) == 6


def test_target_profile_bad_basis_gates_raises(valid_program_spec):
    """Test raising ValueError when giving basis_gates with non-OPENQASM action type."""
    for experiment_type in [ExperimentType.AHS, None]:
        with pytest.raises(ValidationError):
            create_target_profile(
                experiment_type=experiment_type,
                basis_gates=["x", "y", "z"],
                program_spec=valid_program_spec,
            )


def test_target_profile_getitem(target_profile_openqasm):
    """Test the __getitem__ method of TargetProfile."""
    assert target_profile_openqasm["device_id"] == "device123"
    assert target_profile_openqasm["simulator"] is True
    assert target_profile_openqasm["experiment_type"] == ExperimentType.GATE_MODEL
    assert target_profile_openqasm["basis_gates"] == {"gpi", "gpi2", "ms"}


def test_duplicate_basis_gates_removed(valid_program_spec):
    """Test that duplicate basis gates are removed."""
    profile = create_target_profile(
        experiment_type=ExperimentType.GATE_MODEL,
        basis_gates=["X", "x", "x", "Y", "z"],
        program_spec=valid_program_spec,
    )
    assert profile["basis_gates"] == {"x", "y", "z"}


def test_basis_gates_none():
    """Test that passing None to basis_gates does not raise an error."""
    profile = TargetProfile(device_id="1234", simulator=True, basis_gates=None)
    assert profile.basis_gates is None
