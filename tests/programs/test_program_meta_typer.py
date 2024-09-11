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
Unit tests for the typer module

"""

from unittest.mock import patch

import pytest

from qbraid.programs.exceptions import QasmError
from qbraid.programs.typer import (
    BaseQasmInstanceMeta,
    IonQDict,
    IonQDictInstanceMeta,
    Qasm2Instance,
    Qasm2String,
    Qasm3Instance,
    Qasm3String,
    QasmString,
    ValidationError,
)

valid_qasm2_string = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
swap q[0],q[1];
"""

valid_qasm3_string = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[1] q;
z q[0];
"""

invalid_qasm_string = "Some random string"


@pytest.mark.parametrize(
    "cls, string",
    [
        (Qasm2String, valid_qasm2_string),
        (Qasm3String, valid_qasm3_string),
    ],
)
def test_qasm_string_valid(cls, string):
    """Test that the Qasm2String and Qasm3String classes can be instantiated with valid strings."""
    assert isinstance(cls(string), cls)


@pytest.mark.parametrize(
    "cls, string, error",
    [
        (Qasm2String, valid_qasm3_string, ValueError),
        (Qasm3String, invalid_qasm_string, QasmError),
    ],
)
def test_qasm_string_invalid(cls, string, error):
    """Test that the Qasm2String and Qasm3String classes raise an error
    when instantiated with invalid strings."""
    with pytest.raises(error):
        cls(string)


@pytest.mark.parametrize(
    "meta, string",
    [
        (Qasm2Instance, valid_qasm2_string),
        (Qasm3Instance, valid_qasm3_string),
    ],
)
def test_isinstance_checks_valid(meta, string):
    """Test that the isinstance function correctly identifies valid OpenQASM strings."""
    assert isinstance(string, meta)


@pytest.mark.parametrize(
    "meta, version, string",
    [
        (Qasm2Instance, 2, valid_qasm3_string),
        (Qasm3Instance, 3, invalid_qasm_string),
    ],
)
def test_isinstance_checks_invalid(meta, version, string):
    """Test that the isinstance function correctly identifies invalid OpenQASM strings."""
    with patch("qbraid.programs.typer.extract_qasm_version", return_value=version + 1):
        assert not isinstance(string, meta)


def test_qasm_string_type_error():
    """Test that the QasmString class raises a TypeError when instantiated with an invalid type."""
    with pytest.raises(TypeError, match="OpenQASM strings must be initialized with a string."):
        QasmString(123)


def test_base_qasm_instance_meta():
    """Test that the BaseQasmInstanceMeta metaclass does not
    recognize dictionaries as instances of its subclasses."""

    class MockQasmInstance(metaclass=BaseQasmInstanceMeta):
        """Mock class for testing the BaseQasmInstanceMeta metaclass."""

    assert not isinstance({}, MockQasmInstance)


def test_not_qasm_string():
    """Test that the isinstance function returns False when given a non-QasmString object."""
    assert not isinstance("Not a QasmString", Qasm2Instance)


@pytest.mark.parametrize(
    "qasm_instance_class, version",
    [
        (Qasm2Instance, 2),
        (Qasm3Instance, 3),
    ],
)
def test_qasm_instance_properties(qasm_instance_class, version):
    """Test that the QasmInstance class has the correct properties for different versions."""
    assert qasm_instance_class.version == version
    assert qasm_instance_class.__alias__ == f"qasm{version}"
    assert qasm_instance_class.__bound__ == str


def test_ionq_dict_instance_meta_alias():
    """Test that __alias__ property returns the correct alias."""
    assert IonQDict.__alias__ == "ionq"


def test_ionq_dict_instance_meta_bound():
    """Test that __bound__ property returns dict."""
    assert IonQDict.__bound__ == dict


def test_ionq_isinstance_valid_instance():
    """Test that the isinstance function correctly identifies valid IonQDict instances."""
    circuit = {
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }
    assert isinstance(circuit, IonQDict)


@pytest.mark.parametrize(
    "invalid_instance",
    [
        {"qubits": 2, "circuit": [{"gate": 123, "target": 0}]},
        {"qubits": 2, "circuit": [{"gate": "rx", "rotation": "invalid", "target": 0}]},
        {"qubits": 2, "circuit": [{"gate": "cx", "target": "invalid"}]},
        {"qubits": 2, "circuit": [{"gate": "cx", "target": 0, "control": "invalid"}]},
        {"qubits": "invalid", "circuit": [{"gate": "cx", "target": 0}]},
        {"qubits": 2, "circuit": "invalid"},
        {"qubits": 2, "circuit": [{"gate": "cx", "target": 0, "control": 1}, 42]},
    ],
)
def test_ionq_instancecheck_invalid_instances(invalid_instance):
    """Test various invalid instances of IonQDictInstanceMeta."""
    assert not isinstance(invalid_instance, IonQDict)


@pytest.mark.parametrize(
    "single, multiple, field_name",
    [
        (1, None, "target"),
        (None, [1, 2], "control"),
        (1, None, "target"),
        (None, [1, 2, 3], "target"),
    ],
)
def test_ionq_dict_instance_meta_validate_field_valid_cases(single, multiple, field_name):
    """Test _validate_field with valid single and multiple fields."""
    IonQDictInstanceMeta._validate_field(single=single, multiple=multiple, field_name=field_name)


@pytest.mark.parametrize(
    "single, multiple, field_name",
    [
        (1, [2, 3], "target"),
        ("invalid", None, "target"),
        (None, "invalid", "target"),
        (None, [1, "invalid", 3], "target"),
    ],
)
def test_ionq_dict_instance_meta_validate_field_invalid_cases(single, multiple, field_name):
    """Test _validate_field raises ValidationError for invalid input cases."""
    with pytest.raises(ValidationError):
        IonQDictInstanceMeta._validate_field(single, multiple, field_name)
