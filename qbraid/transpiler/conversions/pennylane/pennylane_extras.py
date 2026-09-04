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
Module containing PennyLane conversion extras.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.transpiler.annotations import requires_extras

if TYPE_CHECKING:
    import braket.circuits
    import cirq
    import pennylane.tape
    import qiskit.circuit


@requires_extras("pennylane_qiskit")
def pennylane_to_qiskit(tape: pennylane.tape.QuantumTape) -> qiskit.circuit.QuantumCircuit:
    """Returns a Qiskit QuantumCircuit equivalent to the input PennyLane tape.

    Args:
        tape (pennylane.tape.QuantumTape): PennyLane tape to convert to a Qiskit circuit.

    Returns:
        qiskit.circuit.QuantumCircuit: Qiskit circuit equivalent to input PennyLane tape.
    """
    # pylint: disable-next=import-outside-toplevel
    from pennylane_qiskit.converter import circuit_to_qiskit

    return circuit_to_qiskit(tape, len(tape.wires), diagonalize=False, measure=False)


@requires_extras("braket.pennylane_plugin")
def pennylane_to_braket(tape: pennylane.tape.QuantumTape) -> braket.circuits.Circuit:
    """Returns an Amazon Braket circuit equivalent to the input PennyLane tape.

    Args:
        tape (pennylane.tape.QuantumTape): PennyLane tape to convert to a Braket circuit.

    Returns:
        braket.circuits.Circuit: Braket circuit equivalent to input PennyLane tape.
    """
    # pylint: disable-next=import-outside-toplevel
    from braket.circuits import Circuit, Instruction, Qubit

    # pylint: disable-next=import-outside-toplevel
    from braket.pennylane_plugin.translation import translate_operation

    circuit = Circuit()
    for op in tape.operations:
        braket_gate = translate_operation(op)
        qubits = [Qubit(int(w)) for w in op.wires]
        circuit.add_instruction(Instruction(braket_gate, qubits))
    return circuit


@requires_extras("pennylane_cirq")
def pennylane_to_cirq(tape: pennylane.tape.QuantumTape) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input PennyLane tape.

    Args:
        tape (pennylane.tape.QuantumTape): PennyLane tape to convert to a Cirq circuit.

    Returns:
        cirq.Circuit: Cirq circuit equivalent to input PennyLane tape.
    """
    import pennylane_cirq  # pylint: disable=import-outside-toplevel

    dev = pennylane_cirq.SimulatorDevice(wires=range(len(tape.wires)))
    dev.reset()
    dev.apply(tape.operations)
    return dev.circuit
