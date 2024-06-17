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

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceActionType, DeviceType
from qbraid.runtime.profile import TargetProfile


@pytest.fixture
def valid_program_spec() -> ProgramSpec:
    """Fixture to provide a valid ProgramSpec instance."""
    return ProgramSpec(program_type=str, alias="qasm2")


@pytest.fixture
def valid_target_profile(valid_program_spec) -> TargetProfile:
    """Fixture to provide a valid TargetProfile instance."""
    return TargetProfile(
        device_id="device123",
        device_type=DeviceType.SIMULATOR,
        action_type=DeviceActionType.OPENQASM,
        num_qubits=5,
        program_spec=valid_program_spec,
        provider_name="Heisenberg",
    )


@pytest.mark.parametrize(
    "device_type_str, expected_type",
    [
        ("SIMULATOR", "SIMULATOR"),
        ("QPU", "QPU"),
        ("LOCAL_SIMULATOR", "LOCAL_SIMULATOR"),
    ],
)
def test_target_profile_creation_with_string_type(
    device_type_str, expected_type, valid_program_spec
):
    """Ensure that the constructor correctly interprets string inputs for device_type
    by mapping them to the appropriate DeviceType enum."""
    profile = TargetProfile(
        device_id="device123",
        device_type=device_type_str,
        num_qubits=5,
        program_spec=valid_program_spec,
    )
    assert profile["device_type"] == expected_type


def test_target_profile_raise_for_bad_input():
    """
    Test that the TargetProfile constructor raises appropriate TypeError
    or ValueError for invalid inputs.
    """
    with pytest.raises(TypeError):
        TargetProfile(device_id=123, device_type=DeviceType.SIMULATOR)
    with pytest.raises(ValueError):
        TargetProfile(device_id="device123", device_type="invalid_type")
    with pytest.raises(ValueError):
        TargetProfile(device_id="device123", device_type="SIMULATOR", action_type="invalid_action")
    with pytest.raises(TypeError):
        TargetProfile(device_id="device123", device_type=DeviceType.SIMULATOR, num_qubits="five")
    with pytest.raises(TypeError):
        TargetProfile(
            device_id="device123", device_type=DeviceType.SIMULATOR, program_spec="not_a_spec"
        )
    with pytest.raises(TypeError):
        TargetProfile(device_id="device123", device_type=DeviceType.SIMULATOR, provider_name=10)


def test_target_profile_len(valid_target_profile):
    """Test the __len__ method of TargetProfile"""
    assert len(valid_target_profile) == 6


def test_target_profile_str(valid_target_profile):
    """Test the __str__ method of TargetProfile."""
    expected_str = (
        "{'device_id': 'device123', "
        "'device_type': 'SIMULATOR', "
        "'action_type': 'OPENQASM', "
        "'num_qubits': 5, "
        "'program_spec': <ProgramSpec('qasm2', builtins)>, "
        "'provider_name': 'Heisenberg'}"
    )
    assert str(valid_target_profile).startswith(expected_str)


def test_target_profile_getitem(valid_target_profile):
    """Test the __getitem__ method of TargetProfile."""
    assert valid_target_profile["device_id"] == "device123"
    assert valid_target_profile["device_type"] == "SIMULATOR"
