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
Module defining Qrisp conversions

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

qrisp = LazyLoader("qrisp", globals(), "qrisp")

if TYPE_CHECKING:
    import pytket as pytket_
    import qrisp as qrisp_


@weight(1)
def qrisp_to_pytket(qrisp_qc: qrisp_.QuantumCircuit) -> pytket_.Circuit:
    """Returns a PyTKET circuit equivalent to the input Qrisp circuit.

    Args:
        qrisp_qc: Qrisp circuit to convert to a PyTKET circuit.

    Returns:
        PyTKET Circuit equivalent to the input Qrisp circuit.
    """
    from pytket.circuit import Qubit  # pylint: disable=import-outside-toplevel

    circuit = qrisp_qc.to_pytket()
    # qrisp gives each qubit a register of its own, named after the qubit, and pytket orders
    # qubits by register name as text, so ``qb_100`` would come before ``qb_99`` and the circuit
    # would act on the wrong qubits. One register in qrisp's order keeps the two aligned.
    by_name = {qubit.reg_name: qubit for qubit in circuit.qubits}
    ordered = [by_name.get(str(qubit.identifier)) for qubit in qrisp_qc.qubits]
    if len(by_name) == len(ordered) and all(qubit is not None for qubit in ordered):
        circuit.rename_units({old: Qubit("q", index) for index, old in enumerate(ordered)})
    return circuit
