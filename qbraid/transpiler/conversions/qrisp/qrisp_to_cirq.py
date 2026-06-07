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

cirq = LazyLoader("cirq", globals(), "cirq")
qrisp = LazyLoader("qrisp", globals(), "qrisp")

if TYPE_CHECKING:
    import qrisp as qrisp_
    from cirq import Circuit


@weight(1)
def qrisp_to_cirq(qrisp_qc: qrisp_.QuantumCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Qrisp circuit.

    Args:
        qrisp_qc: Qrisp circuit to convert to a Cirq circuit.

    Returns:
        Cirq Circuit object equivalent to the input Qrisp circuit.
    """
    circuit = qrisp_qc.to_cirq()
    # qrisp emits extended-precision (numpy.longdouble) gate exponents, which cirq's QASM
    # exporter cannot format ("Invalid format specifier 'half_turns'"). Recast them to
    # plain Python float so downstream to_qasm() works.
    normalized = cirq.Circuit()
    for op in circuit.all_operations():
        gate = op.gate
        exponent = getattr(gate, "_exponent", None)
        if exponent is not None and not isinstance(exponent, (int, float)):
            global_shift = float(getattr(gate, "_global_shift", 0.0))
            try:
                gate = type(gate)(exponent=float(exponent), global_shift=global_shift)
            except TypeError:
                gate = type(gate)(exponent=float(exponent))
        normalized.append(gate.on(*op.qubits))
    return normalized
