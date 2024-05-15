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
Unit tests for BraketDevice class

"""
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from braket.aws.queue_information import QueueDepthInfo, QueueType
from braket.circuits import Circuit
from qiskit import QuantumCircuit as QiskitCircuit

from qbraid.programs import ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile
from qbraid.runtime.braket import BraketDevice
from qbraid.runtime.exceptions import ProgramValidationError

from .fixtures import SV1_ARN, TestDevice


def test_device_wrapper_id_error(braket_provider):
    """Test raising device wrapper error due to invalid device ID."""
    with pytest.raises(ValueError):
        braket_provider.get_device("Id123")


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_device_profile_attributes(mock_aws_device):
    """Test that device profile attributes are correctly set."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    assert device.id == profile.get("device_id")
    assert device.num_qubits == profile.get("num_qubits")
    assert device._target_spec == profile.get("program_spec")
    assert device.device_type == DeviceType(profile.get("device_type"))


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_queue_depth(mock_aws_device):
    """Test getting queue_depth BraketDevice"""
    mock_aws_device.queue_depth.return_value = QueueDepthInfo(
        quantum_tasks={QueueType.NORMAL: "19", QueueType.PRIORITY: "3"},
        jobs="0 (3 prioritized job(s) running)",
    )
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    queue_depth = device.queue_depth()
    assert isinstance(queue_depth, int)


@patch("qbraid.runtime.braket.device.AwsDevice")
def test_circuit_too_many_qubits(mock_aws_device):
    """Test that run method raises exception when input circuit
    num qubits exceeds that of wrapped AWS device."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        device_type=DeviceType.SIMULATOR,
        num_qubits=34,
        program_spec=ProgramSpec(Circuit),
        provider_name="Amazon Braket",
        device_id=SV1_ARN,
    )
    device = BraketDevice(profile)
    num_qubits = device.num_qubits + 10
    circuit = QiskitCircuit(num_qubits)
    circuit.h([0, 1])
    circuit.cx(0, num_qubits - 1)
    with pytest.raises(ProgramValidationError):
        device.run(circuit)


def test_aws_device_available(braket_provider):
    """Test BraketDeviceWrapper avaliable output identical"""
    with (
        patch("qbraid.runtime.braket.provider.AwsDevice") as mock_aws_device,
        patch("qbraid.runtime.braket.device.AwsDevice") as mock_aws_device_2,
    ):
        mock_aws_device.return_value = TestDevice(SV1_ARN)
        mock_aws_device_2.return_value = TestDevice(SV1_ARN)
        device = braket_provider.get_device(SV1_ARN)
        is_available_bool, is_available_time, iso_str = device.availability_window()
        assert is_available_bool == device._device.is_available
        assert len(is_available_time.split(":")) == 3
        assert isinstance(iso_str, str)
        try:
            datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pytest.fail("iso_str not in expected format")
