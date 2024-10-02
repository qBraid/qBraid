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
Unit tests for runtime noise model class.

"""
from threading import Thread

import pytest

from qbraid.runtime.noise import NoiseModel


def test_noise_model_initialization():
    """Test the initialization of a noise model."""
    model = NoiseModel("no_noise")
    assert model.value == "no_noise"
    assert (
        model.description
        == "The simulation is performed without any noise, representing an ideal quantum computer."
    )
    assert str(model) == "no_noise"


def test_noise_model_synonym():
    """Test the initialization of a noise model using a synonym."""
    model = NoiseModel("ideal")
    assert model.value == "no_noise"
    assert (
        model.description
        == "The simulation is performed without any noise, representing an ideal quantum computer."
    )
    assert str(model) == "no_noise"


def test_noise_model_equality():
    """Test the equality of noise models."""
    model1 = NoiseModel("no_noise")
    model2 = NoiseModel("ideal")
    assert model1 == model2
    assert model1 == "no_noise"
    assert model2 == "ideal"
    assert model1 != "depolarizing"


def test_noise_model_invalid_name():
    """Test the initialization of a noise model with an invalid name."""
    with pytest.raises(ValueError):
        NoiseModel("invalid@name")


def test_noise_model_register():
    """Test the registration of a custom noise model."""
    model = NoiseModel.register("custom_noise", "A custom noise model.")
    assert model.value == "custom_noise"
    assert model.description == "A custom noise model."
    assert "custom_noise" in NoiseModel._noise_models


def test_noise_model_register_existing_without_overwrite():
    """Test the registration of an existing noise model without permission to overwrite."""
    with pytest.raises(ValueError):
        NoiseModel.register("no_noise", "Trying to overwrite without permission.")


def test_noise_model_register_existing_with_overwrite():
    """Test the registration of an existing noise model with permission to overwrite."""
    model = NoiseModel.register("no_noise", "Overwritten noise model.", overwrite=True)
    assert model.description == "Overwritten noise model."


def test_noise_model_register_synonym():
    """Test the registration of a synonym for an existing noise model."""
    NoiseModel.register_synonym("noiseless", "no_noise")
    model = NoiseModel("noiseless")

    assert model.value == "no_noise"
    assert model.description == "Overwritten noise model."


def test_noise_model_register_synonym_nonexistent_canonical():
    """Test the registration of a synonym for a nonexistent noise model."""
    with pytest.raises(ValueError):
        NoiseModel.register_synonym("nonexistent_synonym", "nonexistent_model")


def test_noise_model_list_registered():
    """Test the listing of registered noise models."""
    registered = NoiseModel.list_registered()
    assert "no_noise" in registered
    assert "depolarizing" in registered


def test_noise_model_list_synonyms():
    """Test the listing of synonyms for noise models."""
    synonyms = NoiseModel.list_synonyms()
    assert synonyms.get("ideal") == "no_noise"


def test_thread_safety_register():
    """Test the thread safety of registering a noise model."""

    def register_noise():
        NoiseModel.register("thread_noise", "A noise model registered in a thread.", overwrite=True)

    threads = [Thread(target=register_noise) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    model = NoiseModel("thread_noise")
    assert model.value == "thread_noise"
    assert model.description == "A noise model registered in a thread."
