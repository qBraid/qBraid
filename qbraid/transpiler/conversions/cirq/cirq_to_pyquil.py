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
Module containing function to convert from Cirq's circuit
representation to pyQuil's circuit representation (Quil programs).

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cirq import LineQubit, QubitOrder
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

try:
    from .cirq_quil_output import QuilOutput
except ImportError:  # pragma: no cover
    QuilOutput = None

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    import cirq.circuits
    from pyquil import Program


@weight(0.74)
def cirq_to_pyquil(circuit: cirq.circuits.Circuit) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
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
        return pyquil.Program(quil_str)
    except ValueError as err:
        raise ProgramConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err
