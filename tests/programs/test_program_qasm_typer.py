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
Unit tests for the qasm_typer module

"""

from unittest.mock import patch

import pytest

from qbraid.programs.exceptions import QasmError
from qbraid.programs.qasm_typer import Qasm2Instance, Qasm2String, Qasm3Instance, Qasm3String

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
    with patch("qbraid.programs.qasm_typer.extract_qasm_version", return_value=version + 1):
        assert not isinstance(string, meta)
