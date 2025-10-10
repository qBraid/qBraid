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
from braket.circuits import Circuit
from braket.circuits.serialization import IRType

from qbraid.passes.qasm import replace_gate_names
from qbraid.transpiler.annotations import weight


@weight(1)
def braket_to_qasm3(circuit: Circuit) -> str:
    """Converts a ``braket.circuits.Circuit`` to an OpenQASM 3.0 string.

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM 3.0 string equivalent to the circuit

    Raises:
        ProgramConversionError: If braket to qasm conversion fails

    """
    has_measurements = any(str(instr.operator) == "Measure" for instr in circuit.instructions)
    qasm_program = circuit.to_ir(IRType.OPENQASM).source
    qasm_module = pyqasm.loads(qasm_program)
    qasm_module.unroll(external_gates=["cnot"])

    if not has_measurements:
        qasm_module.remove_measurements()

    qasm_str = pyqasm.dumps(qasm_module)
    qasm_str = replace_gate_names(qasm_str, {"cx": "cnot"})

    return qasm_str
