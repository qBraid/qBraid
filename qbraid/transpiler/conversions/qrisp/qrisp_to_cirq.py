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


_UNMAPPED_GATES = ("cy", "u3")


def _contains_unmapped(op: qrisp_.Operation) -> bool:
    if op.name in _UNMAPPED_GATES:
        return True
    return op.definition is not None and any(_contains_unmapped(i.op) for i in op.definition.data)


def _inline_unmapped(qrisp_qc: qrisp_.QuantumCircuit) -> qrisp_.QuantumCircuit:
    """Inline the composite gates that contain a ``cy`` or ``u3``, at any depth.

    Qrisp's Cirq converter inlines composites itself, after the rewrites below have run,
    so a nested ``cy`` or ``u3`` would otherwise still reach it.
    """
    if not any(_contains_unmapped(instr.op) for instr in qrisp_qc.data):
        return qrisp_qc
    # pylint: disable-next=import-outside-toplevel
    from qrisp.circuit.transpiler import transpile

    # cy and u3 themselves are kept: the rewrites below handle them exactly.
    return transpile(
        qrisp_qc,
        transpile_predicate=lambda op: op.name not in _UNMAPPED_GATES and _contains_unmapped(op),
    )


def _decompose_u3(qrisp_qc: qrisp_.QuantumCircuit) -> qrisp_.QuantumCircuit:
    """Rewrite each ``u3`` as rz-ry-rz plus its global phase.

    Qrisp's Cirq converter has no mapping for ``u3`` and can't decompose it, but
    qiskit_to_qrisp lowers phase gates (sdg, tdg, p, u1) to ``u3``.
    """
    if not any(instr.op.name == "u3" for instr in qrisp_qc.data):
        return qrisp_qc

    decomposed = qrisp_qc.clearcopy()
    for instr in qrisp_qc.data:
        if instr.op.name != "u3":
            decomposed.append(instr.op, instr.qubits, instr.clbits)
            continue
        theta, phi, lam = instr.op.params
        qubit = instr.qubits[0]
        decomposed.rz(lam, qubit)
        decomposed.ry(theta, qubit)
        decomposed.rz(phi, qubit)
        decomposed.gphase((phi + lam) / 2 + instr.op.global_phase, qubit)
    return decomposed


def _decompose_cy(qrisp_qc: qrisp_.QuantumCircuit) -> qrisp_.QuantumCircuit:
    """Rewrite each ``cy`` as ``s_dg``-``cx``-``s`` on the target (exact, no phase).

    Qrisp's Cirq converter has no mapping for ``cy`` and can't decompose it, but
    qiskit_to_qrisp keeps ``cy`` in its basis.
    """
    if not any(instr.op.name == "cy" for instr in qrisp_qc.data):
        return qrisp_qc

    decomposed = qrisp_qc.clearcopy()
    for instr in qrisp_qc.data:
        if instr.op.name != "cy":
            decomposed.append(instr.op, instr.qubits, instr.clbits)
            continue
        control, target = instr.qubits
        # An open control (ctrl_state "0") is X-conjugated, since qrisp's cx is closed.
        open_control = getattr(instr.op, "ctrl_state", "1") == "0"
        if open_control:
            decomposed.x(control)
        decomposed.s_dg(target)
        decomposed.cx(control, target)
        decomposed.s(target)
        if open_control:
            decomposed.x(control)
    return decomposed


@weight(1)
def qrisp_to_cirq(qrisp_qc: qrisp_.QuantumCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Qrisp circuit.

    Args:
        qrisp_qc: Qrisp circuit to convert to a Cirq circuit.

    Returns:
        Cirq Circuit object equivalent to the input Qrisp circuit.
    """
    circuit = _decompose_cy(_decompose_u3(_inline_unmapped(qrisp_qc))).to_cirq()
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
