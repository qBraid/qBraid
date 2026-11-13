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
Unit tests for converting Braket circuits with gate modifiers via pytket-braket

"""
import pytest
from braket.circuits import Circuit, Instruction
from braket.circuits import gates as braket_gates

from qbraid.interface import circuits_allclose
from qbraid.transpiler import transpile
from qbraid.transpiler.conversions.braket import braket_to_pytket
from qbraid.transpiler.exceptions import ProgramConversionError

pytest.importorskip("pytket.extensions.braket")
pytest.importorskip("qiskit")


@pytest.mark.parametrize(
    "instr",
    [
        Instruction(braket_gates.S(), target=1, control=0),
        Instruction(braket_gates.S(), target=1, power=2),
    ],
)
def test_braket_to_pytket_modifier_raises(instr):
    """Test that modifiers pytket-braket would drop raise instead"""
    with pytest.raises(ProgramConversionError):
        braket_to_pytket(Circuit().add_instruction(instr))


@pytest.mark.parametrize(
    "instr, expected",
    [
        (
            Instruction(braket_gates.S(), target=1, control=0, power=3),
            Circuit().add_instruction(Instruction(braket_gates.Si(), target=1, control=0)),
        ),
        (
            Instruction(braket_gates.X(), target=2, control=[0, 1], control_state=[0, 1]),
            Circuit().x(0).ccnot(0, 1, 2).x(0),  # pylint: disable=no-member
        ),
        (
            Instruction(braket_gates.CPhaseShift(0.5), target=[0, 1], power=-1),
            Circuit().cphaseshift(0, 1, -0.5),  # pylint: disable=no-member
        ),
    ],
)
def test_transpile_braket_modifiers_to_qiskit(instr, expected):
    """Test that a circuit with modifiers transpiles to an equivalent Qiskit circuit"""
    qiskit_circuit = transpile(Circuit().add_instruction(instr), "qiskit")
    assert circuits_allclose(qiskit_circuit, expected)
