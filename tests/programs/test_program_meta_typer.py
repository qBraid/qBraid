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
from pyqasm.exceptions import QasmParsingError

from qbraid.programs.typer import (
    BaseQasmInstanceMeta,
    IonQDict,
    IonQDictInstanceMeta,
    ProgramValidationError,
    Qasm2KirinString,
    Qasm2String,
    Qasm2StringType,
    Qasm3String,
    Qasm3StringType,
    QasmStringType,
    QuboCoefficientsDict,
    get_qasm_type_alias,
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

valid_qasm2_kirin_string = """
KIRIN {cf,func,py.ilist,qasm2.core,qasm2.expr,qasm2.glob,qasm2.indexing,qasm2.inline,qasm2.noise,qasm2.parallel,qasm2.uop};
include "qelib1.inc";
qreg qreg[4];
CX qreg[0], qreg[1];
reset qreg[0];
parallel.CZ {
  qreg[0], qreg[2];
  qreg[1], qreg[3];
}
"""

invalid_qasm_string = "Some random string"


@pytest.mark.parametrize(
    "cls, string",
    [
        (Qasm2StringType, valid_qasm2_string),
        (Qasm3StringType, valid_qasm3_string),
    ],
)
def test_qasm_string_valid(cls, string):
    """Test that the Qasm2StringType and Qasm3StringType
    classes can be instantiated with valid strings."""
    assert isinstance(cls(string), cls)


@pytest.mark.parametrize(
    "cls, string, error",
    [
        (Qasm2StringType, valid_qasm3_string, ValueError),
        (Qasm3StringType, invalid_qasm_string, QasmParsingError),
    ],
)
def test_qasm_string_invalid(cls, string, error):
    """Test that the Qasm2StringType and Qasm3StringType classes raise an error
    when instantiated with invalid strings."""
    with pytest.raises(error):
        cls(string)


@pytest.mark.parametrize(
    "meta, string",
    [
        (Qasm2String, valid_qasm2_string),
        (Qasm3String, valid_qasm3_string),
        (Qasm2KirinString, valid_qasm2_kirin_string),
    ],
)
def test_isinstance_checks_valid(meta, string):
    """Test that the isinstance function correctly identifies valid OpenQASM strings."""
    assert isinstance(string, meta)


def test_get_qasm_type_alias_kirin():
    """Test that get_qasm_type_alias returns the correct alias for KIRIN strings."""
    alias = get_qasm_type_alias(valid_qasm2_kirin_string)
    assert alias == "qasm2_kirin"  # pylint: disable=comparison-with-callable


@pytest.mark.parametrize(
    "meta, version, string",
    [
        (Qasm2String, 2, valid_qasm3_string),
        (Qasm3String, 3, invalid_qasm_string),
    ],
)
def test_isinstance_checks_invalid(meta, version, string):
    """Test that the isinstance function correctly identifies invalid OpenQASM strings."""
    with patch("pyqasm.analyzer.Qasm3Analyzer.extract_qasm_version", return_value=version + 1):
        assert not isinstance(string, meta)


def test_qasm_string_type_error():
    """Test that the QasmString class raises a TypeError when instantiated with an invalid type."""
    with pytest.raises(TypeError, match="OpenQASM strings must be initialized with a string."):
        QasmStringType(123)


def test_base_qasm_instance_meta():
    """Test that the BaseQasmInstanceMeta metaclass does not
    recognize dictionaries as instances of its subclasses."""

    class MockQasmInstance(metaclass=BaseQasmInstanceMeta):
        """Mock class for testing the BaseQasmInstanceMeta metaclass."""

    assert not isinstance({}, MockQasmInstance)


def test_base_qasm_instance_meta_alias():
    """Test that the BaseQasmInstanceMeta metaclass has the correct alias."""

    class FakeQasmInstance(metaclass=BaseQasmInstanceMeta):
        """Fake instance class for testing"""

    assert FakeQasmInstance.__alias__ is None


def test_not_qasm_string():
    """Test that the isinstance function returns False when given a non-QasmString object."""
    assert not isinstance("Not a QasmString", Qasm2String)


@pytest.mark.parametrize(
    "qasm_instance_class, version",
    [
        (Qasm2String, 2),
        (Qasm3String, 3),
    ],
)
def test_qasm_instance_properties(qasm_instance_class, version):
    """Test that the QasmInstance class has the correct properties for different versions."""
    assert qasm_instance_class.version == version
    assert qasm_instance_class.__alias__ == f"qasm{version}"
    assert qasm_instance_class.__bound__ is str


def test_ionq_dict_instance_meta_alias():
    """Test that __alias__ property returns the correct alias."""
    assert IonQDict.__alias__ == "ionq"  # pylint: disable=comparison-with-callable


def test_ionq_dict_instance_meta_bound():
    """Test that __bound__ property returns dict."""
    assert IonQDict.__bound__ is dict  # pylint: disable=comparison-with-callable


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
    """Test _validate_field raises ProgramValidationError for invalid input cases."""
    with pytest.raises(ProgramValidationError):
        IonQDictInstanceMeta._validate_field(single, multiple, field_name)


def test_qubo_coefficients_dict_valid():
    """Test with a valid QUBO coefficients dictionary."""
    valid_dict = {
        ("s1", "s1"): -160.0,
        ("s4", "s2"): 16.0,
        ("s3", "s1"): 224.0,
        ("s2", "s2"): -96.0,
        ("s4", "s1"): 32.0,
        ("s1", "s2"): 64.0,
        ("s3", "s2"): 112.0,
        ("s3", "s3"): -196.0,
        ("s4", "s4"): -52.0,
        ("s4", "s3"): 56.0,
    }
    assert isinstance(valid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_invalid_key_type():
    """Test with an invalid key type (non-tuple key)."""
    invalid_dict = {"s1": -160.0}  # Invalid because key is not a tuple
    assert not isinstance(invalid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_invalid_key_tuple_elements():
    """Test with a tuple key containing non-string elements."""
    invalid_dict = {
        (1, "s2"): 32.0,  # Invalid because one element in the tuple is not a string
        ("s3", 3): 64.0,  # Invalid because one element in the tuple is not a string
    }
    assert not isinstance(invalid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_invalid_key_tuple_length():
    """Test with a tuple key of incorrect length."""
    invalid_dict = {
        ("s1",): -160.0,  # Invalid because tuple length is 1
        ("s2", "s3", "s4"): 96.0,  # Invalid because tuple length is 3
    }
    assert not isinstance(invalid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_invalid_value_type():
    """Test with a value that is not a float."""
    invalid_dict = {
        ("s1", "s2"): 64.0,
        ("s3", "s3"): "string",  # Invalid because the value is not a float
    }
    assert not isinstance(invalid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_empty():
    """Test with an empty dictionary, which should be invalid."""
    empty_dict = {}
    assert not isinstance(empty_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_nested_invalid():
    """Test with a nested dictionary, which should be invalid."""
    nested_invalid_dict = {
        ("s1", "s1"): -160.0,
        ("s2", "s2"): {"nested_key": 32.0},  # Invalid because the value is a dict, not a float
    }
    assert not isinstance(nested_invalid_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_non_dict_type_invalid():
    """Test with a non-dictionary type, which should be invalid."""
    non_dict = "string"
    assert not isinstance(non_dict, QuboCoefficientsDict)


def test_qubo_coefficients_dict_instance_meta_alias():
    """Test that __alias__ property returns the correct alias."""
    assert QuboCoefficientsDict.__alias__ == "qubo"  # pylint: disable=comparison-with-callable


def test_qubo_coefficients_dictt_instance_meta_bound():
    """Test that __bound__ property returns dict."""
    assert QuboCoefficientsDict.__bound__ is dict  # pylint: disable=comparison-with-callable
