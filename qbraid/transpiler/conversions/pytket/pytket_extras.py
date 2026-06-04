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
Module containing PyTKET conversion extras.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

pytket_braket = LazyLoader("pytket_braket", globals(), "pytket.extensions.braket")
pytket_qiskit = LazyLoader("pytket_qiskit", globals(), "pytket.extensions.qiskit")
pytket_cirq = LazyLoader("pytket_cirq", globals(), "pytket.extensions.cirq")
pytket_qir = LazyLoader("pytket_qir", globals(), "pytket.qir")
pyqir = LazyLoader("pyqir", globals(), "pyqir")

if TYPE_CHECKING:
    import braket.circuits
    import cirq
    import pyqir
    import pytket.circuit
    import qiskit


@requires_extras("pytket.extensions.braket")
def pytket_to_braket(circuit: pytket.circuit.Circuit) -> braket.circuits.Circuit:
    """Returns an Amazon Braket circuit equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to Braket circuit.

    Returns:
        braket.circuits.Circuit: Braket circuit equivalent to input pytket circuit.
    """
    braket_circuit, _, _ = pytket_braket.braket_convert.tk_to_braket(circuit)
    return braket_circuit


@requires_extras("pytket.extensions.qiskit")
def pytket_to_qiskit(circuit: pytket.circuit.Circuit) -> qiskit.QuantumCircuit:
    """Returns a Qiskit QuantumCircuit equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to a Qiskit circuit.

    Returns:
        qiskit.QuantumCircuit: Qiskit circuit equivalent to input pytket circuit.
    """
    return pytket_qiskit.tk_to_qiskit(circuit)


@requires_extras("pytket.extensions.cirq")
def pytket_to_cirq(circuit: pytket.circuit.Circuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to a Cirq circuit.

    Returns:
        cirq.Circuit: Cirq circuit equivalent to input pytket circuit.
    """
    return pytket_cirq.tk_to_cirq(circuit)


@requires_extras("pytket.qir", "pyqir")
def pytket_to_pyqir(circuit: pytket.circuit.Circuit) -> pyqir.Module:
    """Returns a PyQIR module equivalent to the input pytket circuit.

    Args:
        circuit (pytket.circuit.Circuit): PyTKET circuit to convert to a PyQIR module.

    Returns:
        pyqir.Module: PyQIR module equivalent to input pytket circuit.
    """
    llvm_ir = pytket_qir.pytket_to_qir(circuit, qir_format=pytket_qir.QIRFormat.STRING)
    context = pyqir.Context()
    return pyqir.Module.from_ir(context, llvm_ir, "Circuit")
