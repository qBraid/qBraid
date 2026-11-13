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
Module for converting Braket circuits to OpenQASM 3.0

"""
import pyqasm
from braket.circuits import Circuit, Instruction
from braket.circuits.gates import Unitary
from braket.circuits.serialization import IRType

from qbraid.passes.qasm import replace_gate_names
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError


def _invert_negative_powers(circuit: Circuit) -> Circuit:
    """Return the circuit with each negative power replaced by a positive power of the
    gate's adjoint, since pyqasm ignores ``inv @`` on gates it decomposes, such as
    ``cphaseshift`` and ``pswap``.
    """
    if all(instr.power >= 0 for instr in circuit.instructions):
        return circuit
    inverted = Circuit()
    for instr in circuit.instructions:
        if instr.power < 0:
            adjoint = instr.operator.adjoint()
            if len(adjoint) != 1:
                raise ProgramConversionError(f"Cannot invert {instr} as a single gate.")
            instr = Instruction(
                adjoint[0],
                instr.target,
                control=instr.control,
                control_state=instr.control_state,
                power=-instr.power,
            )
        inverted.add_instruction(instr)
    for result_type in circuit.result_types:
        inverted.add_result_type(result_type)
    return inverted


@weight(1)
def braket_to_qasm3(circuit: Circuit) -> str:
    """Converts a ``braket.circuits.Circuit`` to an OpenQASM 3.0 string.

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM 3.0 string equivalent to the circuit

    Raises:
        ProgramConversionError: If braket to qasm conversion fails, or the circuit has a
            ``Unitary`` with a power or control modifier, which Braket's OpenQASM export drops.

    """
    circuit = _invert_negative_powers(circuit)
    for instr in circuit.instructions:
        if isinstance(instr.operator, Unitary) and (instr.control or instr.power != 1):
            raise ProgramConversionError(
                f"Braket's OpenQASM export drops the power and control modifiers of {instr}."
            )
    has_measurements = any(str(instr.operator) == "Measure" for instr in circuit.instructions)
    qasm_program = circuit.to_ir(IRType.OPENQASM).source
    qasm_module = pyqasm.loads(qasm_program)
    qasm_module.unroll(external_gates=["cnot"])

    if not has_measurements:
        qasm_module.remove_measurements()

    qasm_str = pyqasm.dumps(qasm_module)
    qasm_str = replace_gate_names(qasm_str, {"cx": "cnot"})

    return qasm_str
