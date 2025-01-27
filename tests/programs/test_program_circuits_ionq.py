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
Unit tests for qbraid.programs.ionq.IonQProgram

"""
import json

import numpy as np
import pytest

from qbraid.interface.random import random_circuit
from qbraid.interface.random.ionq_random import create_gateset_ionq
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.ionq import GateSet, InputFormat, IonQProgram
from qbraid.programs.typer import IonQDict


@pytest.fixture
def ionq_dict() -> IonQDict:
    """Return a valid IonQDict object."""
    return {
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }


@pytest.fixture
def ionq_program(ionq_dict: IonQDict) -> IonQProgram:
    """Return an IonQProgram object."""
    return IonQProgram(ionq_dict)


def test_ionq_program_bits(ionq_program: IonQProgram):
    """Test the qubits and clbits properties."""
    assert ionq_program.num_qubits == 3
    assert ionq_program.num_clbits == 0


def test_ionq_program_serialize(ionq_program: IonQProgram, ionq_dict: IonQDict):
    """Test the qubits and clbits properties."""
    assert ionq_program.serialize() == {"ionqCircuit": json.dumps(ionq_dict)}


def test_ionq_program_type_error():
    """Test that an error is raised when the input is not an IonQDict object."""
    invalid_program = {"qubits": 3, "circuit": 42}
    with pytest.raises(ProgramTypeError):
        IonQProgram(invalid_program)


def test_ionq_program_determine_gateset_raises():
    """Test that an error is raised when determining
    the gateset of a circuit that mixes native and
    abstract (qis) gates."""
    circuit = [
        {"gate": "h", "target": 0},
        {"gate": "cnot", "control": 0, "target": 1},
        {"gate": "cnot", "control": 0, "target": 2},
        {"gate": "gpi", "phase": 0, "target": 0},
    ]

    with pytest.raises(ValueError) as excinfo:
        IonQProgram.determine_gateset(circuit)
    assert "Invalid gate" in str(excinfo.value)


def test_ionq_program_determine_gateset_native():
    """Test that the native gateset is determined correctly."""
    circuit = [
        {"gate": "gpi", "phase": 0, "target": 0},
        {"gate": "gpi2", "phase": 0, "target": 1},
    ]
    assert IonQProgram.determine_gateset(circuit) == GateSet.NATIVE


def test_ionq_program_determine_gateset_empty_circuit():
    """Test that ValueError is raised when determining the gateset of an empty circuit."""
    with pytest.raises(ValueError) as excinfo:
        _ = IonQProgram.determine_gateset([])
    assert "Circuit is empty. Must contain at least one gate." in str(excinfo.value)


def test_ionq_dict_checks_invalid_gateset_type(ionq_dict):
    """Test that an dict object with an invalid gateset type
    is not considered a valid IonQDict instance."""
    ionq_dict_invalid = ionq_dict.copy()
    ionq_dict_invalid["gateset"] = 42
    assert isinstance(ionq_dict, IonQDict)
    assert not isinstance(ionq_dict_invalid, IonQDict)


def test_ionq_dict_checks_invalid_format(ionq_dict):
    """Test that an dict object with an invalid format type
    is not considered a valid IonQDict instance."""
    ionq_dict_invalid = ionq_dict.copy()
    ionq_dict_invalid["format"] = 42
    assert isinstance(ionq_dict, IonQDict)
    assert not isinstance(ionq_dict_invalid, IonQDict)


def test_input_format_enum():
    """Test the InputFormat enumeration."""
    assert len(list(InputFormat)) == 4
    assert InputFormat.CIRCUIT.value == "ionq.circuit.v0"
    assert InputFormat.QASM.value == "qasm"
    assert InputFormat.OPENQASM.value == "openqasm"
    assert InputFormat.QUIPPER.value == "quipper"


def test_validate_for_gateset(ionq_program: IonQProgram):
    """Test that validate_for_gateset does not raise an error."""
    ionq_program.validate_for_gateset()


def test_validate_for_gateset_raises(ionq_dict: IonQDict):
    """Test that validate_for_gateset raises an error when the circuit contains an invalid gate."""
    ionq_dict_invalid = ionq_dict.copy()
    ionq_dict_invalid["circuit"][0]["gate"] = "not_a_gate"

    ionq_program = IonQProgram(ionq_dict_invalid)

    with pytest.raises(ValueError) as excinfo:
        ionq_program.validate_for_gateset()
    assert "Invalid gate" in str(excinfo.value)


def test_random_circuit_ionq():
    """Test that random_circuit generates a valid IonQ program."""
    rand_program = random_circuit("ionq", max_attempts=1, num_qubits=5, depth=10)
    ionq_program = IonQProgram(rand_program)
    ionq_program.validate_for_gateset()


def test_create_gateset_ionq_max_operands_3_or_more():
    """Test that create_gateset_ionq generates a valid gateset."""
    result = create_gateset_ionq(3)

    assert isinstance(result, np.ndarray)

    assert result.dtype == [("gate", object), ("num_qubits", np.int64), ("num_params", np.int64)]

    expected_gates = {
        "x",
        "y",
        "z",
        "h",
        "s",
        "t",
        "v",
        "si",
        "ti",
        "vi",
        "rx",
        "ry",
        "rz",
        "cx",
        "cy",
        "cz",
        "ch",
        "crx",
        "cry",
        "crz",
        "swap",
        "ccnot",
    }
    actual_gates = set(result["gate"])
    assert actual_gates == expected_gates

    assert len(result) == 22

    assert "ccnot" in result["gate"]

    assert result[result["gate"] == "x"]["num_qubits"][0] == 1
    assert result[result["gate"] == "x"]["num_params"][0] == 0
    assert result[result["gate"] == "rx"]["num_qubits"][0] == 1
    assert result[result["gate"] == "rx"]["num_params"][0] == 1
    assert result[result["gate"] == "cx"]["num_qubits"][0] == 2
    assert result[result["gate"] == "cx"]["num_params"][0] == 0
    assert result[result["gate"] == "crx"]["num_qubits"][0] == 2
    assert result[result["gate"] == "crx"]["num_params"][0] == 1
    assert result[result["gate"] == "ccnot"]["num_qubits"][0] == 3
    assert result[result["gate"] == "ccnot"]["num_params"][0] == 0

    result_4 = create_gateset_ionq(4)
    assert np.array_equal(result, result_4)
