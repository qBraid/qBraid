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
Unit test for quantum program registry

"""

import random
import string
import unittest.mock

import pytest

from qbraid.programs import (
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    ProgramSpec,
    get_program_type_alias,
    register_program_type,
    unregister_program_type,
)
from qbraid.programs.registry import is_registered_alias_native


def generate_unique_key(registry: dict, length: int = 10) -> str:
    """
    Generate a random string that is not already a key in the provided registry.

    """
    attempts = 0
    while attempts < 10:
        new_key = "".join(random.choices(string.ascii_letters + string.digits, k=length))
        if new_key not in registry:
            return new_key.lower()
        attempts += 1

    raise RuntimeError(f"Failed to generate a unique key after {attempts} attempts.")


def test_successful_registration():
    """Test successful registration of a program type"""
    try:
        register_program_type(dict, "dict")
        assert "dict" in QPROGRAM_REGISTRY
        assert QPROGRAM_REGISTRY["dict"] == dict
    finally:
        unregister_program_type("dict")


def test_registration_without_alias():
    """Test registration of a program type without an alias"""
    unregister_program_type("unittest", raise_error=False)
    try:
        register_program_type(unittest.mock.Mock)
        assert "unittest" in QPROGRAM_REGISTRY
        assert QPROGRAM_REGISTRY["unittest"] == unittest.mock.Mock
    finally:
        unregister_program_type("unittest", raise_error=False)


def test_error_on_duplicate_alias():
    """Test error when trying to register a duplicate alias"""
    register_program_type(str, "qasm2")
    with pytest.raises(ValueError) as excinfo:
        register_program_type(int, "qasm2")
    assert "Alias 'qasm2' is already registered with a different type." in str(excinfo.value)


def test_error_on_duplicate_type_different_alias():
    """Test error when trying to register a type with a different alias"""
    register_program_type(str, "custom_str")
    with pytest.raises(ValueError) as excinfo:
        register_program_type(str, "another_str")
    assert "Cannot register more than one additional 'str' type beyond 'qasm2', 'qasm3'." in str(
        excinfo.value
    )


def test_re_registration_same_alias_type():
    """Test re-registration of the same type with the same alias"""
    init_registry_size = len(QPROGRAM_REGISTRY)
    register_program_type(str, "qasm2")
    register_program_type(str, "qasm2")
    assert len(QPROGRAM_REGISTRY) == init_registry_size


def test_get_program_type_alias_alias_library_mismatch():
    """Test getting program type when the alias does not match the module."""
    try:
        register_program_type(unittest.mock.Mock, alias="mock")
        assert get_program_type_alias(unittest.mock.Mock()) == "mock"
    finally:
        unregister_program_type("mock")


def test_overwrite_existing_alias():
    """Test overwriting an existing alias with a new type"""
    try:
        register_program_type(str, "qasm2")
        register_program_type(unittest.mock.Mock, "qasm2", overwrite=True)
        assert QPROGRAM_REGISTRY["qasm2"] == unittest.mock.Mock
    finally:
        register_program_type(str, "qasm2", overwrite=True)


def test_is_alias_registered_native_true():
    """Verify that is_alias_registered_native returns True when
    a native program type is registered with a given alias."""
    register_program_type(str, "qasm2")
    assert is_registered_alias_native("qasm2")


def test_is_alias_registered_native_false():
    """Verify that is_alias_registered_native returns False when the registered
    program type for an alias does not match the native program type."""
    try:
        register_program_type(dict, "qasm2", overwrite=True)
        assert not is_registered_alias_native("qasm2")
    finally:
        register_program_type(str, "qasm2", overwrite=True)


def test_register_via_program_spec():
    """Test registering a program type using ProgramSpec"""
    unregister_program_type("unittest", raise_error=False)
    try:
        spec = ProgramSpec(unittest.mock.Mock)
        assert "unittest" in QPROGRAM_REGISTRY
        assert spec.alias == "unittest"
        assert spec.native is False
        assert spec.program_type == unittest.mock.Mock
    finally:
        unregister_program_type("unittest", raise_error=False)


def test_unregister_program_type_error_handling():
    """Test unregistering a program type with different raise_error settings."""
    alias = generate_unique_key(QPROGRAM_REGISTRY)

    try:
        unregister_program_type(alias, raise_error=False)
    except KeyError:
        pytest.fail("KeyError was raised, but raise_error was set to False")

    with pytest.raises(KeyError):
        unregister_program_type(alias, raise_error=True)


def test_unregister_program_type_unique():
    """Test unregistering a program alias where the
    program type is unique within the registry."""
    QPROGRAM_TYPES.discard(dict)
    assert dict not in QPROGRAM_TYPES
    alias = generate_unique_key(QPROGRAM_REGISTRY)
    register_program_type(dict, alias, overwrite=True)
    assert alias in QPROGRAM_REGISTRY
    assert alias in QPROGRAM_ALIASES
    assert dict in QPROGRAM_TYPES
    unregister_program_type(alias)
    assert alias not in QPROGRAM_REGISTRY
    assert alias not in QPROGRAM_ALIASES
    assert dict not in QPROGRAM_TYPES


def test_unregister_program_type_non_unique():
    """Test unregistering a program alias where the
    program type is not unique within the registry."""
    alias = generate_unique_key(QPROGRAM_REGISTRY)
    register_program_type(str, alias, overwrite=True)
    register_program_type(str, "qasm2", overwrite=True)
    assert alias in QPROGRAM_REGISTRY
    assert alias in QPROGRAM_ALIASES
    assert str in QPROGRAM_TYPES
    unregister_program_type(alias)
    assert alias not in QPROGRAM_REGISTRY
    assert alias not in QPROGRAM_ALIASES
    assert str in QPROGRAM_TYPES
