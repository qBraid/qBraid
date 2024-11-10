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
import pytest

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
