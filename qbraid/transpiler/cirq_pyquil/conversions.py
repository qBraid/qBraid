# Copyright 2023 qBraid
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
Module containing functions to convert between Cirq's circuit
representation and pyQuil's circuit representation (Quil programs).

"""
from cirq import Circuit, LineQubit
from cirq.ops import QubitOrder
from cirq_rigetti.quil_input import circuit_from_quil
from cirq_rigetti.quil_output import QuilOutput
from pyquil import Program

from qbraid.interface.convert_to_contiguous import convert_to_contiguous
from qbraid.transpiler.exceptions import CircuitConversionError


def to_pyquil(circuit: Circuit, compat=True) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    if compat:
        circuit = convert_to_contiguous(circuit, rev_qubits=True)
    input_qubits = circuit.all_qubits()
    max_qubit = max(input_qubits)
    # if we are using LineQubits, keep the qubit labeling the same
    if isinstance(max_qubit, LineQubit):
        qubit_range = max_qubit.x + 1
        qubit_order = LineQubit.range(qubit_range)
    # otherwise, use the default ordering (starting from zero)
    else:
        qubit_order = QubitOrder.DEFAULT
    qubits = QubitOrder.as_qubit_order(qubit_order).order_for(input_qubits)
    operations = circuit.all_operations()
    try:
        quil_str = str(QuilOutput(operations, qubits))
        return Program(quil_str)
    except ValueError as err:
        raise CircuitConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err


def from_pyquil(program: Program, compat=True) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    try:
        circuit = circuit_from_quil(program.out())
        if compat:
            circuit = convert_to_contiguous(circuit, rev_qubits=True)
        return circuit
    except Exception as err:
        raise CircuitConversionError(
            "qBraid transpiler doesn't yet support pyQuil noise gates."
        ) from err
