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
Module for converting Cirq circuits to OpenQASM 3.0 strings.

"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

import cirq
import pyqasm
from cirq import ops

from qbraid._version import __version__ as qbraid_version
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

from .cirq_to_qasm2 import ZPowGate, map_zpow_and_unroll

if TYPE_CHECKING:
    from qbraid.programs.typer import Qasm3StringType


def _decompose_unsupported(circuit: cirq.Circuit) -> cirq.Circuit:
    """Decompose operations that don't support the QASM protocol into
    basis gates that do. Walks the circuit and decomposes any gate
    whose ``_qasm_`` method returns ``None`` (or is absent) until the
    resulting operations all have QASM representations.

    The decomposition is bounded to avoid infinite loops: if an operation
    still cannot be expressed in QASM after ``_MAX_DECOMPOSE_DEPTH``
    rounds it is left in place and will trigger a ``ProgramConversionError``
    later during serialisation.
    """
    _MAX_DECOMPOSE_DEPTH = 10

    def _has_qasm(op: cirq.Operation) -> bool:
        args = cirq.QasmArgs(
            qubit_id_map={q: f"q[{i}]" for i, q in enumerate(sorted(op.qubits))},
            meas_key_id_map={},
        )
        try:
            return cirq.qasm(op, args=args, default=None) is not None
        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _needs_decompose(op: cirq.Operation) -> bool:
        return not _has_qasm(op)

    for _ in range(_MAX_DECOMPOSE_DEPTH):
        if not any(_needs_decompose(op) for op in circuit.all_operations()):
            break
        circuit = cirq.map_operations_and_unroll(
            circuit,
            lambda op, _: (
                cirq.decompose(op, keep=_has_qasm, on_stuck_raise=None)
                if _needs_decompose(op)
                else [op]
            ),
        )

    return circuit


def _cirq_to_qasm2_str(
    circuit: cirq.Circuit,
    header: Optional[str],
    precision: int,
    qubit_order: cirq.QubitOrderOrList,
) -> str:
    """Produce a QASM 2.0 string from a Cirq circuit using Cirq's native
    ``_qasm_`` protocol.  Raises ``ProgramConversionError`` for any gate
    that cannot be serialised even after decomposition.
    """
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    try:
        output = cirq.QasmOutput(
            operations=circuit.all_operations(),
            qubits=qubits,
            header=header or f"Generated from qBraid v{qbraid_version}",
            precision=precision,
            version="2.0",
        )
        return str(output)
    except (ValueError, TypeError) as exc:
        raise ProgramConversionError(
            f"Cirq circuit contains a gate that cannot be expressed in QASM: {exc}"
        ) from exc


@weight(1)
def cirq_to_qasm3(
    circuit: cirq.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: cirq.QubitOrderOrList = ops.QubitOrder.DEFAULT,
) -> Qasm3StringType:
    """Convert a Cirq circuit to an OpenQASM 3.0 string.

    Uses Cirq's native ``_qasm_`` protocol for gate serialisation.  Gates
    that do not natively support QASM are first decomposed into basis gates
    that do.  The intermediate QASM 2.0 representation is then upgraded to
    QASM 3.0 via :mod:`pyqasm`.

    This produces a *direct* ``cirq -> qasm3`` edge in the conversion graph,
    avoiding the two-hop ``cirq -> qasm2 -> qasm3`` path and its extra bias
    cost.  New Cirq gates that implement ``_qasm_`` will be handled
    automatically without any changes to this function.

    Args:
        circuit: Cirq circuit to convert.
        header: Comment placed at the top of the output. Defaults to a
            qBraid version string.
        precision: Number of significant digits used for floating-point
            gate parameters.
        qubit_order: Ordering applied to the circuit's qubits when building
            the output register.

    Returns:
        An OpenQASM 3.0 string equivalent to *circuit*.

    Raises:
        ProgramConversionError: If the circuit contains a gate that has no
            QASM representation and cannot be decomposed into one.
    """
    try:
        circuit = map_zpow_and_unroll(circuit)
        circuit = _decompose_unsupported(circuit)
        qasm2_str = _cirq_to_qasm2_str(circuit, header, precision, qubit_order)
    except ProgramConversionError:
        raise
    except Exception as exc:
        raise ProgramConversionError(
            f"Failed to serialise Cirq circuit: {exc}"
        ) from exc

    try:
        module = pyqasm.loads(qasm2_str)
        return module.to_qasm3(as_str=True)
    except Exception as exc:
        raise ProgramConversionError(
            f"Failed to upgrade intermediate QASM 2.0 to QASM 3.0: {exc}"
        ) from exc
