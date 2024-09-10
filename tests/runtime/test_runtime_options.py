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
Unit tests for the qBraid runtime Options dataclass.

"""
import copy

import pytest

from qbraid.runtime.options import Options


def test_options_initialization():
    """Test that the Options class initializes with dynamic fields."""
    options = Options(transpile=True, custom_field=42)
    assert options.get("transpile") is True
    assert options.get("custom_field") == 42


def test_options_set_and_get_field():
    """Test setting and getting a field using both attribute and dictionary access."""
    options = Options()
    options.transpile = False
    options["custom_field"] = "test_value"

    assert options.transpile is False
    assert options["custom_field"] == "test_value"


def test_options_get_with_fallback():
    """Test get method with a fallback value for non-existent fields."""
    options = Options(transpile=True)
    assert options.get("non_existent", "default") == "default"
    assert options.get("transpile") is True


def test_options_setitem_getitem():
    """Test __setitem__ and __getitem__ for setting and accessing fields."""
    options = Options()
    options["new_field"] = 123
    assert options["new_field"] == 123


def test_options_delitem():
    """Test __delitem__ behavior for deleting dynamic fields but not default ones."""
    options = Options(transpile=True)

    options["custom_field"] = 42
    assert options["custom_field"] == 42

    del options["custom_field"]
    with pytest.raises(KeyError):
        _ = options["custom_field"]

    with pytest.raises(KeyError):
        del options["transpile"]


def test_options_getattr_setattr():
    """Test __getattr__ and __setattr__ for setting and getting attributes."""
    options = Options()
    options.custom_attr = 99
    assert options.custom_attr == 99

    with pytest.raises(AttributeError):
        _ = options.non_existent_attr


def test_options_set_validator_and_validation():
    """Test setting a validator and ensuring validation works properly."""
    options = Options(transpile=True)

    options.set_validator("transpile", lambda x: isinstance(x, bool))

    options.transpile = False
    assert options.transpile is False

    with pytest.raises(ValueError):
        options.transpile = "invalid_value"


def test_options_update_options():
    """Test update_options method for updating multiple options with validation."""
    options = Options()

    options.update_options(transpile=False, custom_field=123)
    options.set_validator("custom_field", lambda x: isinstance(x, int))

    assert options.transpile is False
    assert options["custom_field"] == 123

    with pytest.raises(ValueError):
        options.update_options(custom_field="invalid")


def test_options_repr():
    """Test the __repr__ method for correct string output."""
    options = Options(transpile=True, custom_field=42)
    repr_str = repr(options)
    assert repr_str == "Options(transpile=True, custom_field=42)"


def test_options_get_with_missing_field():
    """Test that missing fields return None if no default is provided."""
    options = Options()
    assert options.get("missing_field") is None


def test_options_setattr_update_through_getattr():
    """Test setting a value using setattr and ensuring it reflects via getattr."""
    options = Options()
    setattr(options, "new_field", "test_value")
    assert getattr(options, "new_field") == "test_value"


def test_options_delitem_non_existent_field():
    """Test __delitem__ raises KeyError when deleting a non-existent field."""
    options = Options(transpile=True)
    with pytest.raises(KeyError):
        del options["non_existent_field"]


def test_options_set_validator_for_non_existent_field():
    """Test setting a validator for a non-existent field raises KeyError."""
    options = Options(transpile=True)
    with pytest.raises(KeyError):
        options.set_validator("non_existent_field", lambda x: isinstance(x, int))


def test_options_validator_applies_only_on_update():
    """Test that validators apply on future updates, not retrospectively."""
    options = Options(custom_field="invalid_value")
    options.set_validator("custom_field", lambda x: isinstance(x, int))

    assert options.custom_field == "invalid_value"

    with pytest.raises(ValueError):
        options.custom_field = "still_invalid"


def test_options_remove_validator():
    """Test that removing a validator allows invalid values."""
    options = Options(transpile=True)

    options.set_validator("transpile", lambda x: isinstance(x, bool))
    with pytest.raises(ValueError):
        options.transpile = "invalid_value"

    del options._validators["transpile"]

    options.transpile = "no_validation_now"
    assert options.transpile == "no_validation_now"


def test_options_multiple_validators():
    """Test that setting multiple validators overwrites the previous one."""
    options = Options(custom_field=10)
    options.set_validator("custom_field", lambda x: isinstance(x, int))

    options.set_validator("custom_field", lambda x: x > 5)

    with pytest.raises(ValueError):
        options.custom_field = 3


def test_options_validator_called_only_on_update():
    """Test that the validator is called only when updating a value."""
    options = Options(transpile=True)
    validation_called = False

    def validator(x):
        nonlocal validation_called
        validation_called = True
        return isinstance(x, bool)

    options.set_validator("transpile", validator)

    options.transpile = False
    assert validation_called is True

    validation_called = False
    options.transpile = False
    assert validation_called is False


def test_options_empty_initialization():
    """Test that the Options class can initialize without arguments."""
    options = Options()
    assert options._fields == {}
    assert options.get("non_existent") is None


def test_options_none_as_value():
    """Test that None can be set and retrieved as a valid field value."""
    options = Options()
    options.custom_field = None
    assert options.custom_field is None
    assert options.get("custom_field") is None


def test_options_reset_default_field():
    """Test that a default field can be reset."""
    options = Options(transpile=True)
    options.transpile = False
    assert options.transpile is False
    options.transpile = True
    assert options.transpile is True


def test_options_dict_property():
    """Test that the __dict__ property returns the internal fields."""
    options = Options(transpile=True, custom_field=42)
    assert options.__dict__ == {"transpile": True, "custom_field": 42}


def test_options_dict_conversion():
    """Test that dict(options) works correctly and returns the internal fields."""
    options = Options(transpile=True, custom_field=42)
    options_dict = dict(options)
    assert options_dict == {"transpile": True, "custom_field": 42}


def test_options_iter_method():
    """Test that __iter__ allows iteration over key-value pairs."""
    options = Options(transpile=True, custom_field=42)

    key_value_pairs = list(iter(options))
    expected_pairs = [("transpile", True), ("custom_field", 42)]

    assert key_value_pairs == expected_pairs


def test_options_len_method():
    """Test that __len__ returns the number of internal fields."""
    options = Options(transpile=True, custom_field=42)
    assert len(options) == 2

    options["new_field"] = "new_value"
    assert len(options) == 3


def test_options_equality_check():
    """Test custom __eq__ method with various edge cases."""
    op1 = Options(x=2)
    op2 = Options(x=2)
    assert op1 == op2

    op1.hello = "world"
    assert op1 != op2

    op2.hello = "world"
    assert op1 == op2

    op1.set_validator("hello", lambda x: isinstance(x, str))
    assert op1 != op2

    op2.set_validator("hello", lambda x: isinstance(x, str))
    assert op1 == op2


def test_options_copy_creates_new_instance():
    """Test that __copy__ creates a new instance of Options."""
    options = Options(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    assert copied_options is not options
    assert isinstance(copied_options, Options)


def test_options_copy_has_same_fields():
    """Test that the copied instance has the same fields as the original."""
    options = Options(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    assert copied_options._fields == options._fields
    assert copied_options["transpile"] == options["transpile"]
    assert copied_options["custom_field"] == options["custom_field"]


def test_options_copy_independent_modification():
    """Test that modifying the copied instance doesn't affect the original."""
    options = Options(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    copied_options["custom_field"] = 100

    assert options["custom_field"] == 42
    assert copied_options["custom_field"] == 100


def test_options_copy_with_validators():
    """Test that validators are copied and work independently on the copy."""
    options = Options(transpile=True)
    options.set_validator("transpile", lambda x: isinstance(x, bool))

    copied_options = copy.copy(options)

    assert "transpile" in copied_options._validators
    assert copied_options._validators["transpile"] is not None

    copied_options.transpile = False
    assert copied_options.transpile is False

    with pytest.raises(ValueError):
        copied_options.transpile = "invalid"

    with pytest.raises(ValueError):
        options.transpile = "invalid"


def test_options_copy_with_dynamic_fields():
    """Test that dynamic fields are copied correctly."""
    options = Options(transpile=True)
    options.dynamic_field = "dynamic_value"

    copied_options = copy.copy(options)

    assert copied_options.dynamic_field == "dynamic_value"

    copied_options.dynamic_field = "modified_value"
    assert copied_options.dynamic_field == "modified_value"
    assert options.dynamic_field == "dynamic_value"


def test_options_reserved_keyword_set_validator():
    """Test that 'set_validator' keyword raises a ValueError."""
    with pytest.raises(
        ValueError, match="The option name 'set_validator' is reserved and cannot be used."
    ):
        Options(set_validator=True)


def test_options_reserved_keyword_validate():
    """Test that 'validate' keyword raises a ValueError."""
    with pytest.raises(
        ValueError, match="The option name 'validate' is reserved and cannot be used."
    ):
        Options(validate=True)


def test_options_reserved_keyword_update_options():
    """Test that 'update_options' keyword raises a ValueError."""
    with pytest.raises(
        ValueError, match="The option name 'update_options' is reserved and cannot be used."
    ):
        Options(update_options=True)


def test_options_reserved_keyword_get():
    """Test that 'get' keyword raises a ValueError."""
    with pytest.raises(ValueError, match="The option name 'get' is reserved and cannot be used."):
        Options(get=True)


def test_options_dunder_keyword():
    """Test that dunder-prefixed keywords raise a ValueError."""
    with pytest.raises(
        ValueError, match="The option name '__hidden' with dunder prefix is not allowed."
    ):
        Options(__hidden=True)


def test_options_valid_keywords():
    """Test that valid keywords do not raise errors."""
    try:
        options = Options(transpile=True, debug=False)
        assert options.transpile is True
        assert options.debug is False
    except ValueError:
        pytest.fail("ValueError raised for valid keywords")
