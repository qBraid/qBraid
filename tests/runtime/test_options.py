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

from qbraid.runtime.options import RuntimeOptions


def test_options_initialization():
    """Test that the Options class initializes with dynamic fields."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    assert options.get("transpile") is True
    assert options.get("custom_field") == 42


def test_options_set_and_get_field():
    """Test setting and getting a field using both attribute and dictionary access."""
    options = RuntimeOptions()
    options.transpile = False
    options["custom_field"] = "test_value"

    assert options.transpile is False
    assert options["custom_field"] == "test_value"


def test_options_get_with_fallback():
    """Test get method with a fallback value for non-existent fields."""
    options = RuntimeOptions(transpile=True)
    assert options.get("non_existent", "default") == "default"
    assert options.get("transpile") is True


def test_options_setitem_getitem():
    """Test __setitem__ and __getitem__ for setting and accessing fields."""
    options = RuntimeOptions()
    options["new_field"] = 123
    assert options["new_field"] == 123


def test_options_delitem():
    """Test __delitem__ behavior for deleting dynamic fields but not default ones."""
    options = RuntimeOptions(transpile=True)

    options["custom_field"] = 42
    assert options["custom_field"] == 42

    del options["custom_field"]
    with pytest.raises(KeyError):
        _ = options["custom_field"]

    with pytest.raises(KeyError):
        del options["transpile"]


def test_options_getattr_setattr():
    """Test __getattr__ and __setattr__ for setting and getting attributes."""
    options = RuntimeOptions()
    options.custom_attr = 99
    assert options.custom_attr == 99

    with pytest.raises(AttributeError):
        _ = options.non_existent_attr


def test_options_set_validator_and_validation():
    """Test setting a validator and ensuring validation works properly."""
    options = RuntimeOptions(transpile=True)

    options.set_validator("transpile", lambda x: isinstance(x, bool))

    options.transpile = False
    assert options.transpile is False

    with pytest.raises(ValueError):
        options.transpile = "invalid_value"


def test_options_update_options():
    """Test update_options method for updating multiple options with validation."""
    options = RuntimeOptions()

    options.update_options(transpile=False, custom_field=123)
    options.set_validator("custom_field", lambda x: isinstance(x, int))

    assert options.transpile is False
    assert options["custom_field"] == 123

    with pytest.raises(ValueError):
        options.update_options(custom_field="invalid")


def test_options_repr():
    """Test the __repr__ method for correct string output."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    repr_str = repr(options)
    assert repr_str == "RuntimeOptions(transpile=True, custom_field=42)"


def test_options_get_with_missing_field():
    """Test that missing fields return None if no default is provided."""
    options = RuntimeOptions()
    assert options.get("missing_field") is None


def test_options_setattr_update_through_getattr():
    """Test setting a value using setattr and ensuring it reflects via getattr."""
    options = RuntimeOptions()
    setattr(options, "new_field", "test_value")
    assert getattr(options, "new_field") == "test_value"


def test_options_delitem_non_existent_field():
    """Test __delitem__ raises KeyError when deleting a non-existent field."""
    options = RuntimeOptions(transpile=True)
    with pytest.raises(KeyError):
        del options["non_existent_field"]


def test_options_remove_validator():
    """Test that removing a validator allows invalid values."""
    options = RuntimeOptions(transpile=True)

    options.set_validator("transpile", lambda x: isinstance(x, bool))
    with pytest.raises(ValueError):
        options.transpile = "invalid_value"

    del options._validators["transpile"]

    options.transpile = "no_validation_now"
    assert options.transpile == "no_validation_now"


def test_options_multiple_validators():
    """Test that setting multiple validators overwrites the previous one."""
    options = RuntimeOptions(custom_field=10)
    options.set_validator("custom_field", lambda x: isinstance(x, int))

    options.set_validator("custom_field", lambda x: x > 5)

    with pytest.raises(ValueError):
        options.custom_field = 3


def test_options_validator_called_only_on_update():
    """Test that the validator is called only when updating a value."""
    options = RuntimeOptions(transpile=True)
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
    options = RuntimeOptions()
    assert options._fields == {}
    assert options.get("non_existent") is None


def test_options_none_as_value():
    """Test that None can be set and retrieved as a valid field value."""
    options = RuntimeOptions()
    options.custom_field = None
    assert options.custom_field is None
    assert options.get("custom_field") is None


def test_options_reset_default_field():
    """Test that a default field can be reset."""
    options = RuntimeOptions(transpile=True)
    options.transpile = False
    assert options.transpile is False
    options.transpile = True
    assert options.transpile is True


def test_options_dict_property():
    """Test that the __dict__ property returns the internal fields."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    assert options.__dict__ == {"transpile": True, "custom_field": 42}


def test_options_dict_conversion():
    """Test that dict(options) works correctly and returns the internal fields."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    options_dict = dict(options)
    assert options_dict == {"transpile": True, "custom_field": 42}


def test_options_iter_method():
    """Test that __iter__ allows iteration over key-value pairs."""
    options = RuntimeOptions(transpile=True, custom_field=42)

    key_value_pairs = list(iter(options))
    expected_pairs = [("transpile", True), ("custom_field", 42)]

    assert key_value_pairs == expected_pairs


def test_options_len_method():
    """Test that __len__ returns the number of internal fields."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    assert len(options) == 2

    options["new_field"] = "new_value"
    assert len(options) == 3


def test_options_equality_check():
    """Test custom __eq__ method with various edge cases."""
    op1 = RuntimeOptions(x=2)
    op2 = RuntimeOptions(x=2)
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
    options = RuntimeOptions(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    assert copied_options is not options
    assert isinstance(copied_options, RuntimeOptions)


def test_options_copy_has_same_fields():
    """Test that the copied instance has the same fields as the original."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    assert copied_options._fields == options._fields
    assert copied_options["transpile"] == options["transpile"]
    assert copied_options["custom_field"] == options["custom_field"]


def test_options_copy_independent_modification():
    """Test that modifying the copied instance doesn't affect the original."""
    options = RuntimeOptions(transpile=True, custom_field=42)
    copied_options = copy.copy(options)

    copied_options["custom_field"] = 100

    assert options["custom_field"] == 42
    assert copied_options["custom_field"] == 100


def test_options_copy_with_validators():
    """Test that validators are copied and work independently on the copy."""
    options = RuntimeOptions(transpile=True)
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
    options = RuntimeOptions(transpile=True)
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
        RuntimeOptions(set_validator=True)


def test_options_reserved_keyword_validate_option():
    """Test that 'validate_option' keyword raises a ValueError."""
    with pytest.raises(
        ValueError, match="The option name 'validate_option' is reserved and cannot be used."
    ):
        RuntimeOptions(validate_option=True)


def test_options_reserved_keyword_update():
    """Test that 'update_options' keyword raises a ValueError."""
    with pytest.raises(
        ValueError, match="The option name 'update_options' is reserved and cannot be used."
    ):
        RuntimeOptions(update_options=True)


def test_options_reserved_keyword_get():
    """Test that 'get' keyword raises a ValueError."""
    with pytest.raises(ValueError, match="The option name 'get' is reserved and cannot be used."):
        RuntimeOptions(get=True)


def test_options_dunder_keyword():
    """Test that dunder-prefixed keywords raise a ValueError."""
    with pytest.raises(
        ValueError, match="The option name '__hidden' with dunder prefix is not allowed."
    ):
        RuntimeOptions(__hidden=True)


def test_options_valid_keywords():
    """Test that valid keywords do not raise errors."""
    try:
        options = RuntimeOptions(transpile=True, debug=False)
        assert options.transpile is True
        assert options.debug is False
    except ValueError:
        pytest.fail("ValueError raised for valid keywords")


def test_options_equality_type_mismatch():
    """Test that equality check returns False for different types."""
    options = RuntimeOptions(transpile=True)
    assert options != "not_options"


def test_merge_non_overlapping_options():
    """Test merging options with non-overlapping fields."""
    options1 = RuntimeOptions(option_a=1)
    options2 = RuntimeOptions(option_b=2)

    options1.merge(options2)

    assert options1.option_a == 1
    assert options1.option_b == 2


def test_merge_new_option_with_validator():
    """Test merging when 'other' has a new option with a validator."""
    options1 = RuntimeOptions(option_a=1)

    options2 = RuntimeOptions(option_b=2)
    options2.set_validator("option_b", lambda x: isinstance(x, int) and x > 0)

    options1.merge(options2)

    assert options1.option_b == 2

    # Validator for option_b should be in place
    with pytest.raises(ValueError):
        options1.option_b = -1


@pytest.mark.parametrize(
    "override_validators, initial_value1, validator1, value2, validator2, test_value, should_raise",
    [
        (
            True,
            1,
            lambda x: isinstance(x, int) and x > 0,
            2,
            lambda x: isinstance(x, int) and x > 1,
            1,
            True,
        ),
        (
            False,
            1,
            lambda x: isinstance(x, int) and x > 0,
            2,
            lambda x: isinstance(x, int) and x > 1,
            1,
            False,
        ),
    ],
)

# pylint: disable-next=too-many-arguments
def test_merge_overlapping_options(
    override_validators,
    initial_value1,
    validator1,
    value2,
    validator2,
    test_value,
    should_raise,
):
    """Test merging options with overlapping fields and validators."""
    options1 = RuntimeOptions(option_a=initial_value1)
    options1.set_validator("option_a", validator1)

    options2 = RuntimeOptions(option_a=value2)
    options2.set_validator("option_a", validator2)

    # Handle potential merge failure
    if not override_validators and not validator1(value2):
        with pytest.raises(ValueError):
            options1.merge(options2, override_validators=override_validators)
        return

    options1.merge(options2, override_validators=override_validators)

    assert options1.option_a == value2

    if should_raise:
        with pytest.raises(ValueError):
            options1.option_a = test_value
    else:
        options1.option_a = test_value
        assert options1.option_a == test_value


def test_merge_existing_option_invalidated_by_new_validator():
    """Test merging when existing option in 'self' is invalid under new validator from 'other'."""
    options1 = RuntimeOptions(option_a=1)
    options1.set_validator("option_a", lambda x: x == 1)

    options2 = RuntimeOptions()
    options2.set_validator("option_a", lambda x: x == 2)

    options2.merge(options1, override_validators=True)

    with pytest.raises(ValueError):
        options2.option_a = 2


def test_merge_preserve_existing_validators():
    """Test merging with override_validators=False to preserve existing validators."""
    options1 = RuntimeOptions(option_a=2)
    options1.set_validator("option_a", lambda x: isinstance(x, int) and x % 2 == 0)

    options2 = RuntimeOptions(option_a=4)  # Even number
    options2.set_validator("option_a", lambda x: isinstance(x, int) and x > 0)

    options1.merge(options2, override_validators=False)

    # Validator from options1 should be preserved
    with pytest.raises(ValueError):
        options1.option_a = 3

    options1.option_a = 6
    assert options1.option_a == 6


def test_merge_override_validators():
    """Test merging with override_validators=True to override existing validators."""
    options1 = RuntimeOptions(option_a=2)
    options1.set_validator("option_a", lambda x: isinstance(x, int) and x % 2 == 0)

    options2 = RuntimeOptions(option_a=3)
    options2.set_validator("option_a", lambda x: isinstance(x, int) and x > 0)

    options1.merge(options2, override_validators=True)

    options1.option_a = 5
    assert options1.option_a == 5

    with pytest.raises(ValueError):
        options1.option_a = -1


def test_merge_with_existing_option_invalid_under_new_validator():
    """Test merging when existing option value is invalid under new validator."""
    options1 = RuntimeOptions(option_a=4)

    options2 = RuntimeOptions(option_a=3)
    options2.set_validator("option_a", lambda x: x % 2 != 0)  # Odd numbers only

    with pytest.raises(
        ValueError, match="Value '4' is not valid for field 'option_a' after merging."
    ):
        options2.merge(options1)


def test_merge_with_no_validators():
    """Test merging when neither 'self' nor 'other' have validators."""
    options1 = RuntimeOptions(option_a="value1")
    options2 = RuntimeOptions(option_b="value2")

    options1.merge(options2)

    assert options1.option_a == "value1"
    assert options1.option_b == "value2"


def test_merge_with_invalid_option_in_other():
    """Test merging when 'other' has an invalid option value according to its own validator."""
    options1 = RuntimeOptions(option_a=1)
    options1.set_validator("option_b", lambda x: x == "valid")

    options2 = RuntimeOptions(option_b="invalid")

    with pytest.raises(
        ValueError, match="Value 'invalid' is not valid for field 'option_b' after merging."
    ):
        options1.merge(options2)


def test_merge_with_multiple_options_and_validators():
    """Test merging multiple options and validators."""
    options1 = RuntimeOptions(option_a=1, option_c=3)
    options1.set_validator("option_a", lambda x: isinstance(x, int))
    options1.set_validator("option_c", lambda x: x in [3, 4, 5])

    options2 = RuntimeOptions(option_b="test", option_c=4)
    options2.set_validator("option_b", lambda x: isinstance(x, str))
    options2.set_validator("option_c", lambda x: x in [4, 5, 6])

    options1.merge(options2, override_validators=True)

    assert options1.option_a == 1
    assert options1.option_b == "test"
    assert options1.option_c == 4

    # Validator from options2 should be in effect for option_c
    with pytest.raises(ValueError):
        options1.option_c = 3  # 3 not in [4, 5, 6]

    options1.option_c = 5  # Should pass
    assert options1.option_c == 5


def test_validate_option_handles_exception():
    """Test that validate_option handles exceptions raised by the validator."""
    options = RuntimeOptions(v=2)
    options.set_validator("v", lambda x: x > 0)
    with pytest.raises(ValueError) as exc:
        options.validate_option("v", "a")
    assert (
        "Validator for field 'v' raised an exception: "
        "'>' not supported between instances of 'str' and 'int'" == str(exc.value)
    )


def test_options_set_validator_for_existing_field():
    """Test setting a validator for an existing field."""
    options = RuntimeOptions(test=True)
    options.set_validator("test", lambda x: isinstance(x, bool))

    assert options.test is True

    with pytest.raises(ValueError):
        options.set_validator("test", lambda x: not isinstance(x, bool))


def test_options_set_validator_for_existing_field_with_invalid_value():
    """Test setting a validator for an existing field with an invalid value."""
    options = RuntimeOptions(custom_field="string")

    with pytest.raises(
        ValueError,
        match="Existing value 'string' for field 'custom_field' is not valid for the new validator",
    ):
        options.set_validator("custom_field", lambda x: isinstance(x, int))


def test_options_set_validator_for_non_existent_field():
    """Test setting a validator for a non-existent field."""
    options = RuntimeOptions()
    options.set_validator("new_field", lambda x: isinstance(x, int))

    assert "new_field" in options._validators


def test_options_validator_applies_to_existing_field():
    """Test that a validator applies to an existing field."""
    options = RuntimeOptions(custom_field=42)
    options.set_validator("custom_field", lambda x: isinstance(x, int) and x > 0)

    assert options.custom_field == 42

    with pytest.raises(ValueError):
        options.custom_field = -1


def test_options_validator_allows_valid_update_to_existing_field():
    """Test that a validator allows a valid update to an existing field."""
    options = RuntimeOptions(custom_field=42)
    options.set_validator("custom_field", lambda x: isinstance(x, int) and x > 0)

    options.custom_field = 100
    assert options.custom_field == 100


def test_options_set_validator_error_message_for_exception():
    """Test that the error message for a validator exception is correct."""
    options = RuntimeOptions(custom_field="string")

    with pytest.raises(
        ValueError,
        match=(
            "Existing value 'string' for field 'custom_field' "
            "raised an exception against the new validator"
        ),
    ):
        options.set_validator("custom_field", lambda x: x > 0)


def test_options_set_validator_error_message_for_invalid_value():
    """Test that the error message for an invalid value is correct."""
    options = RuntimeOptions(custom_field=-5)

    with pytest.raises(
        ValueError,
        match="Existing value '-5' for field 'custom_field' is not valid for the new validator",
    ):
        options.set_validator("custom_field", lambda x: x > 0)


def test_options_set_validator_error_message_with_existing_validator():
    """Test that the error message for an existing validator is correct."""
    options = RuntimeOptions(custom_field=5)
    options.set_validator("custom_field", lambda x: x > 0)

    with pytest.raises(
        ValueError, match="Please delete the field before setting the new validator"
    ):
        options.set_validator("custom_field", lambda x: x < 0)
