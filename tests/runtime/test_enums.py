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
from qbraid.runtime.enums import NoiseModel, NoiseModelWrapper


def test_noise_model_members_exist():
    """Test that all NoiseModel enum members exist."""
    assert NoiseModel.Ideal is not None
    assert NoiseModel.Depolarizing is not None
    assert NoiseModel.AmplitudeDamping is not None
    assert NoiseModel.PhaseDamping is not None
    assert NoiseModel.BitFlip is not None
    assert NoiseModel.PhaseFlip is not None


def test_noise_model_member_values():
    """Test that the NoiseModel enum members have correct string values."""
    assert NoiseModel.Ideal.value == "no_noise"
    assert NoiseModel.Depolarizing.value == "depolarizing"
    assert NoiseModel.AmplitudeDamping.value == "amplitude_damping"
    assert NoiseModel.PhaseDamping.value == "phase_damping"
    assert NoiseModel.BitFlip.value == "bit_flip"
    assert NoiseModel.PhaseFlip.value == "phase_flip"


def test_noise_model_contains():
    """Test that specific string values map to the correct NoiseModel enum members."""
    assert NoiseModel("no_noise") == NoiseModel.Ideal
    assert NoiseModel("depolarizing") == NoiseModel.Depolarizing
    assert NoiseModel("amplitude_damping") == NoiseModel.AmplitudeDamping
    assert NoiseModel("phase_damping") == NoiseModel.PhaseDamping
    assert NoiseModel("bit_flip") == NoiseModel.BitFlip
    assert NoiseModel("phase_flip") == NoiseModel.PhaseFlip


def test_noise_model_iteration():
    """Test that iterating over the NoiseModel enum yields all noise models."""
    noise_models = list(NoiseModel)
    assert noise_models == [
        NoiseModel.Ideal,
        NoiseModel.Depolarizing,
        NoiseModel.AmplitudeDamping,
        NoiseModel.PhaseDamping,
        NoiseModel.BitFlip,
        NoiseModel.PhaseFlip,
        NoiseModel.Other,
    ]


def test_noise_model_length():
    """Test that the NoiseModel enum contains the correct number of members."""
    assert len(NoiseModel) == 7


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
