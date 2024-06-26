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


def create_target_profile(action_type, basis_gates, program_spec):
    """Helper function to create a TargetProfile with given parameters."""
    return TargetProfile(
        device_id="device123",
        device_type=DeviceType.SIMULATOR,
        action_type=action_type,
        num_qubits=5,
        program_spec=program_spec,
        provider_name="Heisenberg",
        basis_gates=basis_gates,
    )


@pytest.fixture
def target_profile_openqasm(valid_program_spec) -> TargetProfile:
    """Fixture to provide a valid TargetProfile instance with OPENQASM action type."""
    return create_target_profile(
        action_type=DeviceActionType.OPENQASM,
        basis_gates=["ms", "gpi", "gpi2"],
        program_spec=valid_program_spec,
    )


@pytest.fixture
def target_profile_ahs(valid_program_spec) -> list[TargetProfile]:
    """Fixture to provide a valid TargetProfile instance with AHS action type."""
    return create_target_profile(
        action_type=DeviceActionType.AHS, basis_gates=None, program_spec=valid_program_spec
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
    with pytest.raises(TypeError):
        TargetProfile(
            device_id="device123",
            device_type=DeviceType.SIMULATOR,
            action_type=DeviceActionType.OPENQASM,
            basis_gates=99,
        )
    with pytest.raises(TypeError):
        TargetProfile(
            device_id="device123",
            device_type=DeviceType.SIMULATOR,
            action_type=DeviceActionType.OPENQASM,
            basis_gates=[None],
        )
    with pytest.raises(ValueError):
        TargetProfile(
            device_id="device123",
            device_type=DeviceType.SIMULATOR,
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
    for action_type in [DeviceActionType.AHS, None]:
        with pytest.raises(ValueError):
            create_target_profile(
                action_type=action_type,
                basis_gates=["x", "y", "z"],
                program_spec=valid_program_spec,
            )


def test_target_profile_str(target_profile_openqasm):
    """Test the __str__ method of TargetProfile."""
    # order of basis_gates is not guaranteed
    basis_gates = target_profile_openqasm["basis_gates"]

    expected_str = (
        "{'device_id': 'device123', "
        "'device_type': 'SIMULATOR', "
        "'action_type': 'OPENQASM', "
        "'num_qubits': 5, "
        "'program_spec': <ProgramSpec('qasm2', builtins)>, "
        "'provider_name': 'Heisenberg', "
        f"'basis_gates': {basis_gates}" + "}"
    )
    assert str(target_profile_openqasm).startswith(expected_str)


def test_target_profile_getitem(target_profile_openqasm):
    """Test the __getitem__ method of TargetProfile."""
    assert target_profile_openqasm["device_id"] == "device123"
    assert target_profile_openqasm["device_type"] == "SIMULATOR"
    assert target_profile_openqasm["action_type"] == "OPENQASM"
    assert target_profile_openqasm["basis_gates"] == {"gpi", "gpi2", "ms"}


def test_duplicate_basis_gates_removed(valid_program_spec):
    """Test that duplicate basis gates are removed."""
    profile = create_target_profile(
        action_type=DeviceActionType.OPENQASM,
        basis_gates=["x", "x", "x", "y", "z"],
        program_spec=valid_program_spec,
    )
    assert profile["basis_gates"] == {"x", "y", "z"}
