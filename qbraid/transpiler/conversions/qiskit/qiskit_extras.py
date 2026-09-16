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
qbraid_qir_qiskit = LazyLoader("qbraid_qir_qiskit", globals(), "qbraid_qir.qiskit")
qiskit_ionq = LazyLoader("qiskit_ionq", globals(), "qiskit_ionq")
pennylane_qiskit = LazyLoader("pennylane_qiskit", globals(), "pennylane_qiskit")

if TYPE_CHECKING:
    import braket.circuits
    import pennylane.tape
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


@requires_extras("qbraid_qir.qiskit")
def qiskit_to_pyqir(circuit: qiskit.circuit.QuantumCircuit) -> pyqir.Module:
    """Return a PyQIR module from a Qiskit quantum circuit.

    Args:
        circuit (QuantumCircuit): Qiskit quantum circuit

    Returns:
        Module: PyQIR module
    """
    return qbraid_qir_qiskit.qiskit_to_qir(circuit)


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

    # qiskit>=2 transpiled against a backend maps a small circuit onto the full physical
    # topology (a 1-qubit circuit becomes 29 qubits with its gate on, say, physical
    # qubit 12). Such a circuit carries a TranspileLayout, whose final_index_layout()
    # is the exact virtual->physical map -- inverting it recovers both the original
    # register width and each gate's original index, including layouts that permute
    # qubit order, which a sorted compaction of the used indices would silently swap.
    # A circuit with no layout was never transpiled: its declared register is the
    # user's own, so idle qubits are kept and indices pass through untouched.
    num_qubits = circuit.num_qubits
    layout = getattr(circuit, "layout", None)
    if layout is not None:
        physical_to_virtual = {
            physical: virtual for virtual, physical in enumerate(layout.final_index_layout())
        }
        num_qubits = len(physical_to_virtual)

        def remap(physical: int) -> int:
            try:
                return physical_to_virtual[physical]
            except KeyError as err:
                raise ValueError(
                    f"Gate on physical qubit {physical} has no source qubit in the "
                    "transpile layout; cannot map the circuit back to its original "
                    "register."
                ) from err

        for gate in instrs:
            for key in ("target", "control"):
                if key in gate:
                    gate[key] = remap(gate[key])
            for key in ("targets", "controls"):
                if key in gate:
                    gate[key] = [remap(idx) for idx in gate[key]]

    return {
        "format": InputFormat.CIRCUIT.value,
        "gateset": kwargs.get("gateset", GateSet.QIS.value),
        "qubits": num_qubits,
        "circuit": instrs,
    }


@requires_extras("pennylane_qiskit")
def qiskit_to_pennylane(
    circuit: qiskit.circuit.QuantumCircuit, **kwargs
) -> pennylane.tape.QuantumTape:
    """Returns a PennyLane tape equivalent to the input Qiskit quantum circuit.

    Args:
        circuit (qiskit.circuit.QuantumCircuit): Qiskit circuit to convert to a PennyLane tape.

    Returns:
        pennylane.tape.QuantumTape: PennyLane tape equivalent to input Qiskit circuit.
    """
    import pennylane as qml  # pylint: disable=import-outside-toplevel

    quantum_fn = pennylane_qiskit.load(circuit)
    with qml.tape.QuantumTape() as tape:
        quantum_fn(**kwargs)
    return tape
