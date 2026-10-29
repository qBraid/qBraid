# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for OpenQASM error descriptions.

"""
import openqasm3
import pytest
from openqasm3.parser import QASM3ParsingError

from qbraid.programs.exceptions import describe_error
from qbraid.programs.typer import explain_unrecognized_qasm
from qbraid.transpiler import ProgramConversionError, transpile


def _parse_error(qasm: str) -> QASM3ParsingError:
    with pytest.raises(QASM3ParsingError) as excinfo:
        openqasm3.parse(qasm)
    return excinfo.value


def test_describe_error_recovers_location_of_empty_parse_error():
    """An empty QASM3ParsingError is described by its offending token, 1-based column."""
    err = _parse_error("OPENQASM 3.0;\nqubit q;\nbox { x q; };\n")
    assert str(err) == ""
    assert describe_error(err) == "syntax error near ';' at line 3, column 13"


def test_describe_error_end_of_program():
    """A program cut short is reported as an unexpected end of program."""
    err = _parse_error("OPENQASM 3.0;\nqubit q;\nh q")
    assert describe_error(err) == "syntax error: unexpected end of program at line 3, column 4"


def test_describe_error_completes_dangling_colon():
    """A wrapper whose message ends in a colon gets the chained parse location appended."""
    cause = _parse_error("OPENQASM 3.0;\nqubit q;\nbox { x q; };\n")
    try:
        raise ValueError("Failed to parse OpenQASM string:") from cause
    except ValueError as err:
        assert describe_error(err) == (
            "Failed to parse OpenQASM string: syntax error near ';' at line 3, column 13"
        )


@pytest.mark.parametrize(
    "err, expected",
    [(ValueError("plain message"), "plain message"), (KeyError(), "KeyError")],
)
def test_describe_error_without_parse_location(err, expected):
    """Messages are kept as-is, and an empty one with no parse cause names its type."""
    assert describe_error(err) == expected


@pytest.mark.parametrize(
    "qasm, expected",
    [
        (
            "qubit q;\nh q;\n",
            "Program not recognised as OpenQASM 2 or 3: no 'OPENQASM 2.0;' or "
            "'OPENQASM 3.0;' header found.",
        ),
        (
            "OPENQASM 4.0;\nqubit q;\n",
            "Program not recognised as OpenQASM 2 or 3: OpenQASM version 4.0 is not supported.",
        ),
        (
            "qubit[2] q\nH q[0]\n",
            "Program not recognised as OpenQASM 2 or 3: no 'OPENQASM 2.0;' or "
            "'OPENQASM 3.0;' header found. OpenQASM 3 parser error: "
            "syntax error near 'H' at line 2, column 1",
        ),
    ],
)
def test_explain_unrecognized_qasm(qasm, expected):
    """The explanation names the header problem and, if any, the parser's reason."""
    assert explain_unrecognized_qasm(qasm) == expected


def test_transpile_error_lists_parse_location_per_path():
    """Each failed conversion path reports the parse location, not an empty message."""
    qasm = "OPENQASM 3.0;\nqubit[1] q;\nbox {\n  x q[0];\n};\n"
    with pytest.raises(ProgramConversionError) as excinfo:
        transpile(qasm, "cirq")
    assert "QASM3ParsingError: syntax error near ';' at line 5, column 2" in str(excinfo.value)
