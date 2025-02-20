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
Unit tests for managing quantum program type aliases.

"""
from unittest.mock import Mock

import pytest

from qbraid.programs._import import _assign_default_type_alias, _get_class
from qbraid.programs.alias_manager import (
    _get_program_type_alias,
    find_str_type_alias,
    get_program_type_alias,
    get_qasm_type_alias,
)
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.exceptions import QasmError as QbraidQasmError
from qbraid.programs.registry import derive_program_type_alias

from ..fixtures import packages_bell

QASM_BELL_DATA = [
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];
cx q[0],q[1];
        """,
        "qasm2",
    ),
    (
        """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
        """,
        "qasm3",
    ),
    (
        """
OPENQASM 3.0;
bit[2] __bits__;
qubit[2] __qubits__;
h __qubits__[0];
cnot __qubits__[0], __qubits__[1];
__bits__[0] = measure __qubits__[0];
__bits__[1] = measure __qubits__[1];
        """,
        "qasm3",
    ),
]

QASM_ERROR_DATA = [
    """
OPENQASM xyz;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0;
cx q[0], q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];

        """,
    """
OPENQASM #@!$;
include "stdgates.inc";
bit c[2];
qubit q[2];
h q[0]
cx q[0], q[1];
measure q -> c;
        """,
]


@pytest.mark.parametrize("qasm_str, expected_version", QASM_BELL_DATA)
def test_get_qasm_type_alias(qasm_str: str, expected_version: str):
    """Test getting QASM version"""
    alias = get_qasm_type_alias(qasm_str)
    assert str(alias) == str(expected_version)


@pytest.mark.parametrize("qasm_str", QASM_ERROR_DATA)
def test_get_qasm_type_alias_error(qasm_str):
    """Test getting QASM version"""
    with pytest.raises(QbraidQasmError):
        get_qasm_type_alias(qasm_str)


@pytest.mark.parametrize("bell_circuit", packages_bell, indirect=True)
def test_get_program_type_alias(bell_circuit):
    """Test that the correct package is returned for a given program."""
    circuit, expected_package = bell_circuit
    package_name = get_program_type_alias(circuit)
    assert package_name == expected_package


@pytest.mark.parametrize("program,expected_package", [(Mock(), "unittest")])
def test_get_program_type_alias_required_supported_false(program, expected_package):
    """Test that None or module name is returned for unsupported package when
    require supported is given as False."""
    package = derive_program_type_alias(program)
    assert package == expected_package


def test_raise_error_unuspported_source_program():
    """Test that an error is raised if source program is not supported."""
    with pytest.raises(ProgramTypeError):
        get_program_type_alias(Mock())


@pytest.mark.parametrize(
    "item",
    ["OPENQASM 1.0; bad operation", "OPENQASM -3.1; bad operation", "DECLARE ro BIT[1]", "circuit"],
)
def test_bad_source_openqasm_program(item):
    """Test raising ProgramTypeError converting invalid OpenQASM program string"""
    with pytest.raises(ProgramTypeError):
        get_program_type_alias(item)


@pytest.mark.parametrize("item", [1, None])
def test_bad_source_program_type(item):
    """Test raising ProgramTypeError converting circuit of non-supported type"""
    with pytest.raises(ProgramTypeError):
        get_program_type_alias(item)


def test_get_program_type_alias_with_type_instead_of_instance():
    """Test error raised when a type rather than an instance is provided."""
    with pytest.raises(ProgramTypeError) as excinfo:
        _get_program_type_alias(int)
    assert "Expected an instance of a quantum program, not a type." in str(excinfo.value)


def test_get_program_type_alias_with_string_returning_package(monkeypatch):
    """Test that a valid string type alias is correctly returned."""
    monkeypatch.setattr(
        "qbraid.programs.alias_manager.find_str_type_alias", lambda: "valid_package"
    )
    monkeypatch.setattr(
        "qbraid.programs.alias_manager.get_qasm_type_alias",
        lambda x: (_ for _ in ()).throw(QbraidQasmError("error")),
    )

    result = _get_program_type_alias("some qasm program string")
    assert (
        result == "valid_package"
    ), "Did not return expected package when valid package is available"


def test_get_program_type_alias_with_multiple_matches(monkeypatch):
    """Test error raised when program matches multiple registered types."""
    monkeypatch.setattr(
        "qbraid.programs.alias_manager.QPROGRAM_REGISTRY", {"type1": Mock, "type2": Mock}
    )
    with pytest.raises(ProgramTypeError) as excinfo:
        _get_program_type_alias(Mock())
    assert "matches multiple registered program types" in str(excinfo.value)


def test_get_program_type_alias_safe_flag_handling():
    """Test handling of 'safe' flag with non-matching program types."""
    result = get_program_type_alias(object(), safe=True)
    assert result is None, "Should return None when safe is True and no matching types are found"


def test_find_single_str_type_alias():
    """Test the case where there is exactly one valid string key."""
    registry = {
        "qasm2": int,
        "qasm3": float,
        "custom_alias": str,
    }
    assert find_str_type_alias(registry) == "custom_alias"


def test_find_str_type_alias_raises_value_error():
    """Test the case where there are multiple valid string keys, expecting a ValueError."""
    registry = {
        "qasm2": int,
        "qasm3": float,
        "alias1": str,
        "alias2": str,
    }
    with pytest.raises(ValueError) as excinfo:
        find_str_type_alias(registry)
    assert "Multiple additional keys with type 'str' found: ['alias1', 'alias2']" in str(
        excinfo.value
    )


def test_find_no_str_type_alias():
    """Test the case where there are no valid string keys."""
    registry = {
        "qasm2": int,
        "qasm3": float,
    }
    assert find_str_type_alias(registry) is None


class SinglePartModule:
    """Test class with a single-part module name."""

    __module__ = "quantum"


class MultiPartModule:
    """Test class with a multi-part module name."""

    __module__ = "parent.child"


class MainModule:
    """Test class with the __main__ module."""

    __module__ = "__main__"


class BuiltinsModule:
    """Test class with the builtins module."""

    __module__ = "builtins"


def test_submodule_multi_part():
    """Check alias creation for multi-part module with submodule flag."""
    assert derive_program_type_alias(MultiPartModule, use_submodule=True) == "parent_child"


def test_submodule_single_part_error():
    """Ensure ValueError for single-part module with submodule flag."""
    with pytest.raises(
        ValueError, match="Module name does not have at least two parts for submodule aliasing."
    ):
        derive_program_type_alias(SinglePartModule, use_submodule=True)


def test_submodule_main_error():
    """Ensure ValueError for __main__ module with submodule flag."""
    with pytest.raises(
        ValueError, match="Cannot use submodule aliasing with __main__ or builtins module."
    ):
        derive_program_type_alias(MainModule, use_submodule=True)


def test_submodule_builtins_error():
    """Ensure ValueError for builtins module with submodule flag."""
    with pytest.raises(
        ValueError, match="Cannot use submodule aliasing with __main__ or builtins module."
    ):
        derive_program_type_alias(BuiltinsModule, use_submodule=True)


def test_submodule_insufficient_error():
    """Ensure ValueError for insufficient module parts with submodule flag."""
    with pytest.raises(
        ValueError, match="Module name does not have at least two parts for submodule aliasing."
    ):
        derive_program_type_alias(SinglePartModule, use_submodule=True)


def test_single_part_module_name():
    """Test alias assignment with a single-part module name."""
    imported_aliases = {"quantum": object}
    alias = _assign_default_type_alias(imported_aliases, SinglePartModule)
    assert alias == "quantum_singlepartmodule"


def test_duplicate_alias_raises_value_error():
    """Ensure ValueError is raised for duplicate alias."""
    imported_aliases = {"quantum": object, "quantum_singlepartmodule": object}
    with pytest.raises(ValueError, match="Duplicate alias quantum_singlepartmodule"):
        _assign_default_type_alias(imported_aliases, SinglePartModule)


def test_get_ionq_program_type_alias():
    """Test getting the IonQ program type alias."""
    circuit = {
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }
    assert _get_program_type_alias(circuit) == "ionq"


def test_get_class_none_for_unsupported_program():
    """Test that None is returned for unsupported program type module."""
    with pytest.raises(ValueError) as excinfo:
        _get_class("not a module")
    assert "Unsupported module 'not a module'" == str(excinfo.value)
