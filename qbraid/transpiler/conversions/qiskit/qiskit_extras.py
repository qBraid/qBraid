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
Module defining Qiskit conversion extras.

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qiskit_braket_provider = LazyLoader("qiskit_braket_provider", globals(), "qiskit_braket_provider")
qiskit_qir = LazyLoader("qiskit_qir", globals(), "qiskit_qir")
qiskit_ionq = LazyLoader("qiskit_ionq", globals(), "qiskit_ionq")

if TYPE_CHECKING:
    import braket.circuits
    import pyqir
    import qiskit.circuit

    import qbraid.programs


@requires_extras("qiskit_braket_provider")
def qiskit_to_braket(circuit: qiskit.circuit.QuantumCircuit, **kwargs) -> braket.circuits.Circuit:
    """Return a Braket quantum circuit from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit
        basis_gates (Optional[Iterable[str]]): The gateset to transpile to.
            If `None`, the transpiler will use all gates defined in the Braket SDK.
            Default: `None`.
        verbatim (bool): Whether to translate the circuit without any modification, in other
            words without transpiling it. Default: False.

    Returns:
        Circuit: Braket circuit
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return qiskit_braket_provider.providers.adapter.to_braket(circuit, **kwargs)


@requires_extras("qiskit_qir")
def qiskit_to_pyqir(circuit: qiskit.circuit.QuantumCircuit) -> pyqir.Module:
    """Return a PyQIR module from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit

    Returns:
        Module: PyQIR module
    """
    # tuple of module and list of entry points
    module, _ = qiskit_qir.to_qir_module(circuit)
    return module


@requires_extras("qiskit_ionq")
def qiskit_to_ionq(circuit: qiskit.circuit.QuantumCircuit, **kwargs) -> qbraid.programs.IonQDict:
    """Return a IonQDict from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit

    Returns:
        dict: IonQDict representing the circuit
    """
    # pylint: disable-next=import-outside-toplevel
    from qbraid.programs.gate_model.ionq import GateSet, InputFormat

    instrs, _, _ = qiskit_ionq.helpers.qiskit_circ_to_ionq_circ(circuit, **kwargs)
    return {
        "format": InputFormat.CIRCUIT.value,
        "gateset": kwargs.get("gateset", GateSet.QIS.value),
        "qubits": circuit.num_qubits,
        "circuit": instrs,
    }
