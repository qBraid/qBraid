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
Unit tests for runtime noise model classes.

"""

import threading

import pytest

from qbraid.runtime.noise import NoiseModel, NoiseModelSet


def test_noise_model_initialization():
    """Test NoiseModel initialization with valid inputs."""
    model = NoiseModel("ideal")
    assert model.name == "ideal"
    assert model.value == "ideal"
    assert model.description.startswith("The simulation is performed without any noise")

    model_with_desc = NoiseModel("custom", "Custom description")
    assert model_with_desc.name == "custom"
    assert model_with_desc.value == "custom"
    assert model_with_desc.description == "Custom description"


def test_noise_model_normalization():
    """Test that noise model names are normalized correctly."""
    model = NoiseModel("  Ideal Noise ")
    assert model.value == "ideal_noise"


def test_noise_model_invalid_name():
    """Test that invalid noise model names raise ValueError."""
    with pytest.raises(ValueError) as excinfo:
        NoiseModel("Invalid@Name")
    assert "Invalid noise model name" in str(excinfo.value)


def test_noise_model_long_description():
    """Test that overly long descriptions raise ValueError."""
    long_description = "a" * 121
    with pytest.raises(ValueError) as excinfo:
        NoiseModel("ideal", long_description)
    assert "Description must be 120 characters or fewer" in str(excinfo.value)


def test_noise_model_str():
    """Test __str__ method of NoiseModel."""
    model = NoiseModel("ideal")
    assert str(model) == "ideal"


def test_noise_model_repr():
    """Test __repr__ method of NoiseModel."""
    model = NoiseModel("ideal")
    assert repr(model) == "NoiseModel('ideal')"


def test_noise_model_equality():
    """Test equality checks for NoiseModel."""
    model1 = NoiseModel("ideal")
    model2 = NoiseModel("Ideal")
    model3 = NoiseModel("depolarizing")

    assert model1 == model2
    assert model1 != model3
    assert model1 == "ideal"
    assert model1 == "Ideal"
    assert model1 != "depolarizing"
    assert model1 != 123  # Should return NotImplemented


def test_noise_model_hash():
    """Test that NoiseModel instances are hashable."""
    model_set = {NoiseModel("ideal"), NoiseModel("Ideal"), NoiseModel("depolarizing")}
    assert len(model_set) == 2  # "ideal" and "depolarizing"


def test_noise_model_immutability():
    """Test that NoiseModel instances are immutable."""
    model = NoiseModel("ideal")
    with pytest.raises(AttributeError):
        model.value = "new_value"
    with pytest.raises(AttributeError):
        model.description = "new_description"


def test_noise_models_add_and_get():
    """Test adding and retrieving noise models in NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom", "Custom description")

    ideal_model = models.get("ideal")
    assert ideal_model.value == "ideal"

    custom_model = models.get("custom")
    assert custom_model.description == "Custom description"


def test_noise_models_add_existing_no_overwrite():
    """Test adding an existing noise model without overwrite."""
    models = NoiseModelSet()
    models.add("ideal")
    with pytest.raises(ValueError) as excinfo:
        models.add("Ideal", "Different description")
    assert "already exists with a different definition" in str(excinfo.value)


def test_noise_models_add_existing_with_overwrite():
    """Test adding an existing noise model with overwrite."""
    models = NoiseModelSet()
    models.add("ideal", "Original description")
    models.add("Ideal", "New description", overwrite=True)
    ideal_model = models.get("ideal")
    assert ideal_model.description == "New description"


def test_noise_models_remove():
    """Test removing a noise model."""
    models = NoiseModelSet()
    models.add("ideal")
    models.remove("ideal")
    assert "ideal" not in models


def test_noise_models_remove_nonexistent():
    """Test removing a nonexistent noise model."""
    models = NoiseModelSet()
    with pytest.raises(KeyError) as excinfo:
        models.remove("nonexistent")
    assert "Noise model 'nonexistent' not found" in str(excinfo.value)


def test_noise_models_discard():
    """Test discarding a noise model."""
    models = NoiseModelSet()
    models.add("ideal")
    models.discard("ideal")
    assert "ideal" not in models
    models.discard("ideal")  # Should not raise an error


def test_noise_models_clear():
    """Test clearing all noise models."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom")
    models.clear()
    assert len(models) == 0


def test_noise_models_update():
    """Test updating one NoiseModels instance with another."""
    models1 = NoiseModelSet()
    models1.add("ideal")
    models2 = NoiseModelSet()
    models2.add("custom")
    models1.update(models2)
    assert "ideal" in models1
    assert "custom" in models1


def test_noise_models_update_invalid_type():
    """Test updating with an invalid type."""
    models = NoiseModelSet()
    with pytest.raises(TypeError) as excinfo:
        models.update(["ideal"])
    assert "Can only update from a dict or another NoiseModelSet instance" in str(excinfo.value)


def test_noise_models_update_from_dict():
    """Test updating with a dict type."""
    models = NoiseModelSet()
    models.update({"key": "value"})
    assert models.get("key").description == "value"


def test_noise_models_iteration():
    """Test iteration over NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom")
    keys = list(models)
    assert sorted(keys) == ["custom", "ideal"]


def test_noise_models_len():
    """Test len() function on NoiseModels."""
    models = NoiseModelSet()
    assert len(models) == 0
    models.add("ideal")
    assert len(models) == 1


def test_noise_models_contains():
    """Test __contains__ method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    assert "ideal" in models
    assert "Ideal" in models
    assert "nonexistent" not in models


def test_noise_models_getitem():
    """Test __getitem__ method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    ideal_model = models["ideal"]
    assert ideal_model.value == "ideal"
    with pytest.raises(KeyError):
        _ = models["nonexistent"]


def test_noise_models_setitem():
    """Test __setitem__ method of NoiseModels."""
    models = NoiseModelSet()
    model = NoiseModel("ideal")
    models["ideal"] = model
    assert "ideal" in models
    with pytest.raises(ValueError) as excinfo:
        models["ideal"] = "not a NoiseModel"
    assert "Value must be a NoiseModel instance" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        models["different_key"] = model
    assert "Key does not match the NoiseModel's normalized value" in str(excinfo.value)


def test_noise_models_delitem():
    """Test __delitem__ method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    del models["ideal"]
    assert "ideal" not in models
    with pytest.raises(KeyError):
        del models["ideal"]


def test_noise_models_values():
    """Test values() method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom")
    values = list(models.values())
    assert len(values) == 2
    assert all(isinstance(model, NoiseModel) for model in values)


def test_noise_models_items():
    """Test items() method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom")
    items = list(models.items())
    assert len(items) == 2
    for key, model in items:
        assert key == model.value


def test_noise_models_repr():
    """Test __repr__ method of NoiseModels."""
    models = NoiseModelSet()
    models.add("ideal")
    models.add("custom")

    repr_str = repr(models)

    assert repr_str.startswith("NoiseModelSet([")
    assert "'ideal'" in repr_str
    assert "'custom'" in repr_str
    assert repr_str.endswith("])")


def test_noise_model_invalid_equality():
    """Test __eq__ with unsupported type."""
    model = NoiseModel("ideal")
    assert model != 123


def test_noise_models_thread_safety():
    """Test that NoiseModels is thread-safe."""
    models = NoiseModelSet()

    def add_model(name):
        models.add(name)

    threads = []
    for i in range(10):
        t = threading.Thread(target=add_model, args=(f"model_{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(models) == 10


def test_noise_models_invalid_key_in_setitem():
    """Test setting an item with a key that doesn't match the model's value."""
    models = NoiseModelSet()
    model = NoiseModel("ideal")
    with pytest.raises(ValueError) as excinfo:
        models["different_key"] = model
    assert "Key does not match the NoiseModel's normalized value" in str(excinfo.value)


def test_noise_models_pop():
    """Test popping a noise model."""
    models = NoiseModelSet()
    models.add("ideal")
    model = models._models.pop("ideal")
    assert model.value == "ideal"
    assert "ideal" not in models


def test_noise_model_normalize_staticmethod():
    """Test the _normalize static method."""
    assert NoiseModel._normalize("  Ideal Noise ") == "ideal_noise"


def test_noise_model_validate_classmethod():
    """Test the _validate class method."""
    # Valid case
    NoiseModel._validate("ideal_noise", "Valid description")
    # Invalid name
    with pytest.raises(ValueError):
        NoiseModel._validate("invalid@name")
    # Description too long
    long_description = "a" * 121
    with pytest.raises(ValueError):
        NoiseModel._validate("ideal_noise", long_description)


def test_noise_models_add_invalid_model():
    """Test adding a model with invalid name."""
    models = NoiseModelSet()
    with pytest.raises(ValueError):
        models.add("Invalid@Name")


def test_noise_models_get_nonexistent():
    """Test getting a nonexistent noise model."""
    models = NoiseModelSet()
    assert models.get("nonexistent") is None


def test_noise_models_discard_nonexistent():
    """Test discarding a nonexistent noise model."""
    models = NoiseModelSet()
    models.discard("nonexistent")  # Should not raise an error


def test_noise_models_update_with_overlapping_keys():
    """Test updating with overlapping keys."""
    models1 = NoiseModelSet()
    models1.add("ideal")
    models2 = NoiseModelSet()
    models2.add("ideal", "New description")
    models1.update(models2)
    ideal_model = models1.get("ideal")
    assert ideal_model.description == "New description"


def test_noise_models_invalid_type_in_contains():
    """Test __contains__ with invalid key type."""
    models = NoiseModelSet()
    assert 123 not in models


def test_noise_models_lock():
    """Test that the lock is working (indirectly)."""
    models = NoiseModelSet()
    models.add("ideal")

    def remove_model():
        models.remove("ideal")

    with models._lock:
        t = threading.Thread(target=remove_model)
        t.start()
        t.join(timeout=1)
        assert t.is_alive()  # Thread should be blocked


def test_noise_models_from_dict():
    """Test creating NoiseModelSet from a dictionary."""
    data = {"ideal": "Ideal noise model", "custom": "Custom noise model"}
    models = NoiseModelSet.from_dict(data)
    assert len(models) == 2
    assert models.get("ideal").description == "Ideal noise model"
    assert models.get("custom").description == "Custom noise model"
