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

"""
Unit tests for qbraid.programs.pyquil.PyQuilProgram

"""
import pytest

try:
    from pyquil import Program
    from qbraid_core.services.runtime.schemas import Program as RuntimeProgram

    from qbraid.programs.exceptions import ProgramTypeError
    from qbraid.programs.gate_model.pyquil import PyQuilProgram

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True
    RuntimeProgram = None


pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_invalid_program_type():
    """Test raising ProgramTypeError for invalid program type"""
    with pytest.raises(ProgramTypeError):
        PyQuilProgram("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_program_properties():
    """Test properties of PyQuilProgram"""
    program = PyQuilProgram(Program())
    assert program.num_clbits == 0
    assert program.depth == 0


def test_pyquil_program_serialize():
    """Test serialize method of PyQuilProgram"""
    pyquil_program = Program()
    pyquil_program += "H 0"
    pyquil_program += "CNOT 0 1"

    qbraid_program = PyQuilProgram(pyquil_program)
    serialized = qbraid_program.serialize()

    assert isinstance(serialized, RuntimeProgram)
    assert serialized.format == "quil"
    assert "H 0" in serialized.data
    assert "CNOT 0 1" in serialized.data
