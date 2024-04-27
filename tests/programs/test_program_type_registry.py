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

import unittest.mock

import pytest

from qbraid.programs import QPROGRAM_REGISTRY, get_program_type_alias, register_program_type


@pytest.fixture(autouse=True)
def reset_registry():
    """Fixture to reset the registry after each test function completes."""
    # Store the original state of the registry
    original_registry = QPROGRAM_REGISTRY.copy()
    yield  # Yield control to the test function
    # Reset the registry after the test function completes
    QPROGRAM_REGISTRY.clear()
    QPROGRAM_REGISTRY.update(original_registry)


def test_successful_registration():
    """Test successful registration of a program type"""
    register_program_type(dict, "dict")
    assert "dict" in QPROGRAM_REGISTRY
    assert QPROGRAM_REGISTRY["dict"] == dict


def test_registration_without_alias():
    """Test registration of a program type without an alias"""
    register_program_type(unittest.mock.Mock)
    assert "unittest" in QPROGRAM_REGISTRY
    assert QPROGRAM_REGISTRY["unittest"] == unittest.mock.Mock


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
    register_program_type(unittest.mock.Mock, alias="mock")
    assert get_program_type_alias(unittest.mock.Mock()) == "mock"


def test_overwrite_existing_alias():
    """Test overwriting an existing alias with a new type"""
    register_program_type(str, "qasm2")
    register_program_type(unittest.mock.Mock, "qasm2", overwrite=True)
    assert QPROGRAM_REGISTRY["qasm2"] == unittest.mock.Mock
