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
Module defining Amazon Braket conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras
from qbraid.transpiler.exceptions import ProgramConversionError

qiskit_braket_provider = LazyLoader("qiskit_braket_provider", globals(), "qiskit_braket_provider")
pytket_braket = LazyLoader("pytket_braket", globals(), "pytket.extensions.braket")

if TYPE_CHECKING:
    import braket.circuits
    import pytket.circuit
    import qiskit.circuit


@requires_extras("qiskit_braket_provider")
def braket_to_qiskit(circuit: braket.circuits.Circuit) -> qiskit.circuit.QuantumCircuit:
    """Return a Qiskit quantum circuit from a Braket quantum circuit.

    Args:
        circuit (Circuit): Braket quantum circuit

    Returns:
        QuantumCircuit: Qiskit quantum circuit
    """
    return qiskit_braket_provider.providers.adapter.to_qiskit(circuit)


@requires_extras("pytket.extensions.braket")
def braket_to_pytket(circuit: braket.circuits.Circuit) -> pytket.circuit.Circuit:
    """Returns a pytket circuit equivalent to the input Amazon Braket circuit.

    Args:
        circuit (braket.circuits.Circuit): Braket circuit to convert to a pytket circuit.

    Returns:
        pytket.circuit.Circuit: PyTKET circuit object equivalent to input Braket circuit.

    Raises:
        ProgramConversionError: If an instruction has a power or control modifier, which
            pytket-braket drops.
    """
    for instr in circuit.instructions:
        if instr.control or instr.power != 1:
            raise ProgramConversionError(
                f"pytket-braket drops the power and control modifiers of {instr}."
            )
    return pytket_braket.braket_convert.braket_to_tk(circuit)
