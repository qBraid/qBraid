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
Unit tests native runtime device schemas.

"""
from decimal import Decimal

import pytest

from qbraid.runtime.enums import NoiseModel, NoiseModelWrapper
from qbraid.runtime.native.device_schemas import DeviceData


@pytest.fixture
def device_data_qir_simulator():
    """Return a dictionary of device data for the qBraid QIR simulator."""
    return {
        "pricing": {"perTask": 0.005, "perShot": 0, "perMinute": 0.075},
        "numberQubits": 64,
        "pendingJobs": 0,
        "qbraid_id": "qbraid_qir_simulator",
        "name": "QIR sparse simulator",
        "provider": "qBraid",
        "paradigm": "gate-based",
        "type": "SIMULATOR",
        "vendor": "qBraid",
        "runPackage": "pyqir",
        "status": "ONLINE",
        "isAvailable": True,
    }


@pytest.fixture
def device_data_quera_simulator():
    """Return a dictionary of device data for the QuEra QASM simulator."""
    return {
        "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
        "numberQubits": 30,
        "pendingJobs": 0,
        "qbraid_id": "quera_qasm_simulator",
        "name": "Noisey QASM simulator",
        "provider": "QuEra",
        "paradigm": "gate-based",
        "type": "SIMULATOR",
        "vendor": "qBraid",
        "runPackage": "qasm2",
        "status": "ONLINE",
        "isAvailable": True,
    }


@pytest.fixture
def device_data_quera_aquila():
    """Return a dictionary of device data for the QuEra Aquila QPU."""
    return {
        "pricing": {"perTask": 0.3, "perShot": 0.01, "perMinute": 0},
        "numberQubits": 256,
        "pendingJobs": 9,
        "qbraid_id": "aws_quera_aquila",
        "name": "Aquila",
        "provider": "QuEra",
        "paradigm": "AHS",
        "type": "QPU",
        "vendor": "AWS",
        "runPackage": "braket",
        "status": "OFFLINE",
        "isAvailable": False,
    }


def test_device_data_qir_simulator(device_data_qir_simulator):
    """Test DeviceData class for qBraid QIR simulator."""
    device = DeviceData(**device_data_qir_simulator)

    assert device.provider == "qBraid"
    assert device.name == "QIR sparse simulator"
    assert device.paradigm == "gate-based"
    assert device.device_type == "SIMULATOR"
    assert device.num_qubits == 64
    assert device.pricing.perTask == Decimal("0.005")
    assert device.pricing.perShot == Decimal("0")
    assert device.pricing.perMinute == Decimal("0.075")
    assert device.status == "ONLINE"
    assert device.is_available is True


def test_device_data_quera_simulator(device_data_quera_simulator):
    """Test DeviceData class for QuEra QASM simulator."""
    device = DeviceData(**device_data_quera_simulator)

    assert device.provider == "QuEra"
    assert device.name == "Noisey QASM simulator"
    assert device.paradigm == "gate-based"
    assert device.device_type == "SIMULATOR"
    assert device.num_qubits == 30
    assert device.pricing.perTask == Decimal("0")
    assert device.pricing.perShot == Decimal("0")
    assert device.pricing.perMinute == Decimal("0")
    assert device.status == "ONLINE"
    assert device.is_available is True


def test_device_data_quera_aquila(device_data_quera_aquila):
    """Test DeviceData class for QuEra Aquila QPU."""
    device = DeviceData(**device_data_quera_aquila)

    assert device.provider == "QuEra"
    assert device.name == "Aquila"
    assert device.paradigm == "AHS"
    assert device.device_type == "QPU"
    assert device.num_qubits == 256
    assert device.pricing.perTask == Decimal("0.3")
    assert device.pricing.perShot == Decimal("0.01")
    assert device.pricing.perMinute == Decimal("0")
    assert device.status == "OFFLINE"
    assert device.is_available is False


def test_noise_model_standard_enum():
    """Test that standard noise models return correct values."""
    NoiseModelWrapper.reset_other_value()
    assert NoiseModel.Ideal.value == "no_noise"
    assert NoiseModel.Depolarizing.value == "depolarizing"
    assert NoiseModel.AmplitudeDamping.value == "amplitude_damping"
    assert NoiseModel.BitFlip.value == "bit_flip"
    assert NoiseModel.PhaseFlip.value == "phase_flip"
    # assert NoiseModel.Other.value == "quera_lqc_backend"


def test_noise_model_other_default():
    """Test that the default 'Other' noise model returns its original value."""
    NoiseModelWrapper.reset_other_value()
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "other"


def test_set_other_noise_model():
    """Test that the 'Other' noise model value can be dynamically updated."""
    NoiseModelWrapper.set_other_value("custom_noise_model")
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "custom_noise_model"


def test_set_other_noise_model_multiple_times():
    """Test that the 'Other' noise model can be updated multiple times."""
    NoiseModelWrapper.set_other_value("first_custom_noise")
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "first_custom_noise"

    NoiseModelWrapper.set_other_value("second_custom_noise")
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "second_custom_noise"
    NoiseModelWrapper.reset_other_value()


def test_non_other_noise_models_unchanged():
    """Ensure other noise models are not affected by updates to the 'Other' model."""
    NoiseModelWrapper.set_other_value("custom_noise_model")

    assert NoiseModel.Ideal.value == "no_noise"
    assert NoiseModel.Depolarizing.value == "depolarizing"
    assert NoiseModel.AmplitudeDamping.value == "amplitude_damping"
    assert NoiseModel.BitFlip.value == "bit_flip"
    assert NoiseModel.PhaseFlip.value == "phase_flip"


def test_reset_other_noise_model():
    """Test resetting 'Other' noise model to its default value."""
    NoiseModelWrapper.set_other_value("temporary_noise_model")
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "temporary_noise_model"

    NoiseModelWrapper.set_other_value("other")
    assert NoiseModelWrapper.get_noise_model(NoiseModel.Other).value == "other"
