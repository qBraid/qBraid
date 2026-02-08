# Copyright 2025 qBraid
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

# pylint: disable=redefined-outer-name

"""
Unit tests for qbraid.runtime.experiment metadata classes.

"""
import pytest
from pydantic import ValidationError

from qbraid.programs.typer import Qasm2String, Qasm3String
from qbraid.runtime.experiment import (
    AhsExperimentMetadata,
    GateModelExperimentMetadata,
)


def test_gate_model_metadata_qasm_validator_none():
    """Test that qasm validator returns None when value is None."""
    metadata = GateModelExperimentMetadata()
    assert metadata.qasm is None


def test_gate_model_metadata_qasm_validator_raises_for_invalid():
    """Test that qasm validator raises ValueError for invalid QASM type."""
    # Test with openQasm alias (the actual field name in the schema)
    with pytest.raises(ValidationError) as excinfo:
        GateModelExperimentMetadata(openQasm="not a valid qasm string")
    assert "openQasm must be a valid OpenQASM string" in str(excinfo.value)


def test_ahs_metadata_filling_validator_none():
    """Test that filling validator returns None when value is None."""
    metadata = AhsExperimentMetadata()
    assert metadata.filling is None


def test_ahs_metadata_filling_validator_validates_items():
    """Test that filling validator validates each item in the list."""
    # Test with valid filling
    metadata = AhsExperimentMetadata(filling=[0, 1, 0, 1])
    assert metadata.filling == [0, 1, 0, 1]

    # Test with invalid filling values
    with pytest.raises(ValidationError) as excinfo:
        AhsExperimentMetadata(filling=[0, 1, 2, 0])
    assert "Invalid filling value. Must be a list of integers, each either 0 or 1" in str(
        excinfo.value
    )


def test_ahs_metadata_filling_validator_handles_exception():
    """Test that filling validator properly handles ValueError from invalid items."""
    # When non-integers are passed, Pydantic will raise ValidationError for int parsing
    # before the validator runs. But if we pass integers outside 0 or 1, the validator runs.
    with pytest.raises(ValidationError) as excinfo:
        AhsExperimentMetadata(filling=[0, 1, 3, 0])
    assert "Invalid filling value" in str(excinfo.value) or "Must be 0 or 1" in str(excinfo.value)


def test_ahs_metadata_validate_lengths_mismatch():
    """Test that validate_ahs raises ValueError when lengths are inconsistent."""
    with pytest.raises(
        ValueError,
        match="The lengths of 'sites', 'filling', and value of 'num_atoms' must be consistent",
    ):
        AhsExperimentMetadata(sites=[(0.0, 0.0), (1.0, 1.0)], filling=[0, 1, 0], num_atoms=2)


def test_ahs_metadata_validate_sets_num_atoms_from_filtered():
    """Test that validate_ahs sets num_atoms from filtered_lengths when None."""
    metadata = AhsExperimentMetadata(sites=[(0.0, 0.0), (1.0, 1.0)], filling=[0, 1])
    assert metadata.num_atoms == 2


def test_gate_model_metadata_with_valid_qasm2():
    """Test GateModelExperimentMetadata with valid Qasm2String."""
    valid_qasm2 = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
h q[0];"""
    # Use openQasm alias (the actual field name in the schema)
    metadata = GateModelExperimentMetadata(openQasm=valid_qasm2)
    assert isinstance(metadata.qasm, Qasm2String)


def test_gate_model_metadata_with_valid_qasm3():
    """Test GateModelExperimentMetadata with valid Qasm3String."""
    valid_qasm3 = """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];"""
    # Use openQasm alias (the actual field name in the schema)
    metadata = GateModelExperimentMetadata(openQasm=valid_qasm3)
    assert isinstance(metadata.qasm, Qasm3String)
