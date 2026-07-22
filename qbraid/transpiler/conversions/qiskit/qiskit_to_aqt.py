# Copyright 2026 qBraid
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
Module defining the ``qiskit -> aqt`` conversion.

Reduces a qiskit circuit to the AQT native basis ``{RZ, R, RXX}`` — with angles wrapped into the
ranges the arnica API accepts (``R.theta in [0, pi]``, ``R.phi in [0, 2*pi]``,
``RXX.theta in [0, pi/2]``) — and builds a native ``aqt_connector.models.circuits.QuantumCircuit``.
``repetitions`` (shots) is a placeholder here and is set per circuit by
:class:`~qbraid.runtime.aqt.AQTDevice` at submit time.

The angle-wrapping passes (:class:`WrapRxxAngles`, :class:`RewriteRxAsR`) and the gate serializer
(:func:`_qiskit_to_aqt_circuit`) are adapted from ``qiskit-aqt-provider``
(``transpiler_plugin.py``, (C) Copyright Alpine Quantum Technologies GmbH 2023; and
``circuit_to_aqt.py``, (C) Copyright IBM 2019, Alpine Quantum Technologies GmbH 2022), both under
the Apache License 2.0. They have been altered to live in qBraid — applied via an explicit
:class:`~qiskit.transpiler.PassManager` rather than qiskit entry-point plugins — so qBraid does not
depend on the ``qiskit-aqt-provider`` package.

"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from qbraid_core._import import LazyLoader
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate, Instruction
from qiskit.circuit.library import RGate, RXGate, RXXGate, RZGate
from qiskit.circuit.tools import pi_check
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import PassManager
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.transpiler.passes import Decompose, Optimize1qGatesDecomposition

from qbraid.transpiler.annotations import requires_extras

# aqt_connector is an optional (aqt-extra) dependency; this module is imported whenever the qiskit
# conversions load, so defer importing it via LazyLoader to keep the transpiler import-safe.
aqt_circuits = LazyLoader("aqt_circuits", globals(), "aqt_connector.models.circuits")
aqt_operations = LazyLoader("aqt_operations", globals(), "aqt_connector.models.operations")

if TYPE_CHECKING:
    import qiskit.circuit
    from aqt_connector.models.circuits import Circuit
    from aqt_connector.models.circuits import QuantumCircuit as AQTQuantumCircuit

# AQT hardware natively implements this basis: virtual-Z (RZ), single-qubit rotation (R),
# and the Molmer-Sorensen entangler (RXX).
AQT_BASIS_GATES: Final = ["rz", "r", "rxx"]


def rewrite_rx_as_r(theta: float) -> Instruction:
    """Instruction equivalent to ``Rx(theta)`` as ``R(theta, phi)`` with theta in [0, pi]."""
    theta = math.atan2(math.sin(theta), math.cos(theta))
    phi = math.pi if theta < 0.0 else 0.0
    return RGate(abs(theta), phi)


class RewriteRxAsR(TransformationPass):
    """Rewrite ``Rx(theta)`` as ``R(theta, phi)`` with theta in [0, pi] and phi in [0, 2*pi].

    Since the pass needs to determine if the relevant angles are in range, target circuits must
    have all these angles bound when applying the pass.
    """

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Apply the transformation pass."""
        for node in dag.gate_nodes():
            if node.name == "rx":
                (theta,) = node.op.params
                dag.substitute_node(node, rewrite_rx_as_r(float(theta)))
        return dag


@dataclass(frozen=True)
class _CircuitInstruction:
    """Substitute for ``qiskit.circuit.CircuitInstruction`` that allows integer qubits."""

    gate: Gate
    qubits: tuple[int, ...]


def _rxx_positive_angle(theta: float) -> list[_CircuitInstruction]:
    """List of instructions equivalent to ``RXX(theta)`` with theta >= 0."""
    rxx = _CircuitInstruction(RXXGate(abs(theta)), qubits=(0, 1))

    if theta >= 0:
        return [rxx]

    return [
        _CircuitInstruction(RZGate(math.pi), (0,)),
        rxx,
        _CircuitInstruction(RZGate(math.pi), (0,)),
    ]


def _emit_rxx_instruction(theta: float, instructions: list[_CircuitInstruction]) -> Instruction:
    """Collect the passed instructions into a single one labeled ``Rxx(theta)``."""
    qc = QuantumCircuit(2, name=f"{WrapRxxAngles.SUBSTITUTE_GATE_NAME}({pi_check(theta)})")
    for instruction in instructions:
        qc.append(instruction.gate, instruction.qubits)

    return qc.to_instruction()


def wrap_rxx_angle(theta: float) -> Instruction:
    """Instruction equivalent to ``RXX(theta)`` with theta in [0, pi/2]."""
    # fast path if -pi/2 <= theta <= pi/2
    if abs(theta) <= math.pi / 2:
        operations = _rxx_positive_angle(theta)
        return _emit_rxx_instruction(theta, operations)

    # exploit 2-pi periodicity of Rxx
    theta %= 2 * math.pi

    if abs(theta) <= math.pi / 2:
        operations = _rxx_positive_angle(theta)
    elif abs(theta) <= 3 * math.pi / 2:
        corrected_angle = theta - np.sign(theta) * math.pi
        operations = [
            _CircuitInstruction(RXGate(math.pi), (0,)),
            _CircuitInstruction(RXGate(math.pi), (1,)),
        ]
        operations.extend(_rxx_positive_angle(corrected_angle))
    else:
        corrected_angle = theta - np.sign(theta) * 2 * math.pi
        operations = _rxx_positive_angle(corrected_angle)

    return _emit_rxx_instruction(theta, operations)


class WrapRxxAngles(TransformationPass):
    """Wrap ``Rxx`` angles to [0, pi/2]."""

    SUBSTITUTE_GATE_NAME: Final = "Rxx-wrapped"

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Apply the transformation pass."""
        for node in dag.gate_nodes():
            if node.name == "rxx":
                (theta,) = node.op.params

                if 0 <= float(theta) <= math.pi / 2:
                    continue

                rxx = wrap_rxx_angle(float(theta))
                dag.substitute_node(node, rxx)

        return dag


def transpile_to_aqt(
    circuit: qiskit.circuit.QuantumCircuit,
) -> qiskit.circuit.QuantumCircuit:
    """Transpile ``circuit`` to the AQT native basis with API-valid angles.

    Mirrors ``qiskit-aqt-provider``'s ``translation_method="aqt"`` + ``scheduling_method="aqt"``
    stages without depending on that package: a standard translation to ``{rx, rz, rxx}`` followed
    by the ported angle-wrapping passes. The result uses only ``{rz, r, rxx}`` (plus measurement)
    with ``R``/``RXX`` angles in the ranges the arnica API accepts.
    """
    base = transpile(circuit, basis_gates=["rx", "rz", "rxx"], optimization_level=1)
    pass_manager = PassManager(
        [
            # Wrap out-of-range RXX angles into [0, pi/2] (substituting a composite gate) ...
            WrapRxxAngles(),
            # ... then decompose those composites back to primitive gates.
            Decompose([f"{WrapRxxAngles.SUBSTITUTE_GATE_NAME}*"]),
            # Collapse single-qubit runs as ZXZ (virtual Z + a single RX pulse) ...
            Optimize1qGatesDecomposition(basis=["rx", "rz"]),
            # ... then rewrite each RX as an angle-wrapped R.
            RewriteRxAsR(),
        ]
    )
    return pass_manager.run(base)


def _qiskit_to_aqt_circuit(circuit: qiskit.circuit.QuantumCircuit) -> Circuit:
    """Serialize a qiskit circuit already in the AQT native basis into an AQT ``Circuit``.

    Expects only ``{rz, r, rxx}`` gates (plus terminal measurement / barriers) with API-valid
    angles — i.e. the output of :func:`transpile_to_aqt`. Angles are converted from radians to the
    API's units of pi.
    """
    ops: list = []
    num_measurements = 0

    for instruction in circuit.data:
        name = instruction.operation.name
        if name != "measure" and num_measurements > 0:
            raise ValueError(
                "Measurement operations can only be located at the end of the circuit."
            )

        if name == "rz":
            (phi,) = instruction.operation.params
            (qubit,) = instruction.qubits
            ops.append(
                aqt_operations.OperationModel(
                    root=aqt_operations.GateRZ(
                        phi=float(phi) / np.pi, qubit=circuit.find_bit(qubit).index
                    )
                )
            )
        elif name == "r":
            theta, phi = instruction.operation.params
            (qubit,) = instruction.qubits
            ops.append(
                aqt_operations.OperationModel(
                    root=aqt_operations.GateR(
                        phi=float(phi) / np.pi,
                        theta=float(theta) / np.pi,
                        qubit=circuit.find_bit(qubit).index,
                    )
                )
            )
        elif name == "rxx":
            (theta,) = instruction.operation.params
            q0, q1 = instruction.qubits
            ops.append(
                aqt_operations.OperationModel(
                    root=aqt_operations.GateRXX(
                        theta=float(theta) / np.pi,
                        qubits=[circuit.find_bit(q0).index, circuit.find_bit(q1).index],
                    )
                )
            )
        elif name == "measure":
            num_measurements += 1
        elif name == "barrier":
            continue
        else:
            raise ValueError(f"Operation '{name}' not in basis gate set: {{rz, r, rxx}}")

    if not num_measurements:
        raise ValueError("Circuit must have at least one measurement operation.")

    ops.append(aqt_operations.OperationModel(root=aqt_operations.Measure()))
    return aqt_circuits.Circuit(root=ops)


@requires_extras("aqt_connector")
def qiskit_to_aqt(circuit: qiskit.circuit.QuantumCircuit) -> AQTQuantumCircuit:
    """Return a native AQT ``QuantumCircuit`` from a qiskit ``QuantumCircuit``.

    Args:
        circuit (qiskit.circuit.QuantumCircuit): Qiskit quantum circuit.

    Returns:
        aqt_connector.models.circuits.QuantumCircuit: the per-circuit submission unit with the
            circuit reduced to the AQT native basis and ``number_of_qubits`` taken from the
            transpiled register size. ``repetitions`` is a placeholder (``1``); the device sets it
            to the requested shots at submit time.
    """
    transpiled = transpile_to_aqt(circuit)
    return aqt_circuits.QuantumCircuit(
        repetitions=1,
        quantum_circuit=_qiskit_to_aqt_circuit(transpiled),
        number_of_qubits=transpiled.num_qubits,
    )
