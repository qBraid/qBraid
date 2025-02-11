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
Unit test for quantum program registry

"""
import random
import string
import sys
import unittest.mock

import pytest

from qbraid.exceptions import QbraidError
from qbraid.interface import random_circuit
from qbraid.programs import (
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    ProgramSpec,
    derive_program_type_alias,
    get_program_type_alias,
    load_program,
    register_program_type,
    unregister_program_type,
)
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.registry import get_native_experiment_type, is_registered_alias_native
from qbraid.programs.typer import IonQDict


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
        assert QPROGRAM_REGISTRY["dict"] is dict
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
    try:
        register_program_type(str, "custom_str")

        with pytest.raises(ValueError) as excinfo:
            register_program_type(str, "another_str")

        expected_msg = (
            "Cannot register more than one additional 'str' type beyond "
            "'qasm2', 'qasm3', and 'qasm2_kirin'."
        )
        assert expected_msg in str(excinfo.value)
    finally:
        unregister_program_type("custom_str", raise_error=False)
        unregister_program_type("another_str", raise_error=False)


def test_error_on_duplicate_type():
    """Test error when trying to register a type that is already registered"""
    register_program_type(int, "test_type_0")
    with pytest.raises(ValueError):
        register_program_type(int, "test_type_1")

    unregister_program_type("test_type_0", raise_error=False)


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


def test_program_spec_str_rep():
    """Test string representation of ProgramSpec"""
    spec = ProgramSpec(str, alias="qasm2")
    assert str(spec) == "ProgramSpec(str, qasm2)"


def test_program_spec_equality():
    """Test equality of ProgramSpec instances"""
    spec1 = ProgramSpec(str, alias="qasm2")
    spec2 = {}
    assert spec1 != spec2


class FakeType:
    """Fake type for testing automatic alias registration"""

    def __module__(self):
        return None


def test_error_on_automatic_alias():
    """Test error when trying to register a program type with an automatic alias"""
    with pytest.raises(ValueError):
        derive_program_type_alias(FakeType)


def test_derive_program_type_alias_qbraid_meta():
    """Test deriving an alias from a QbraidMetaType instance"""
    assert derive_program_type_alias(IonQDict) == "ionq"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10 or higher")
def test_load_entrypoint_not_found():
    """Test error when trying to load a program type that is not found"""
    with unittest.mock.patch("importlib.metadata.entry_points") as mock_entry_points:
        mock_entry_points.return_value.select.return_value = []
        with pytest.raises(QbraidError):
            program = random_circuit("qiskit")
            load_program(program)


def test_program_type_error():
    """Test the ProgramTypeError class."""
    error = ProgramTypeError(program="test")
    message = error.generate_message()
    assert message == "Quantum program of type '<class 'str'>' is not supported."

    error = ProgramTypeError()
    message = error.generate_message()
    assert message == "Unsupported quantum program type."


def test_get_native_experiment_type_not_found():
    """Test error when trying to get the native experiment type that is not found."""
    with pytest.raises(ValueError) as excinfo:
        get_native_experiment_type("not_found")
    assert "Entry point 'not_found' not found in 'qbraid.programs'." in str(excinfo.value)
