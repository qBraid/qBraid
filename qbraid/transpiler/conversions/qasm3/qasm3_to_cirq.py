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
Module for conversions from QASM 3 to Cirq Circuits

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyqasm
from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.passes.qasm.compat import normalize_if_blocks, replace_gate_names
from qbraid.programs.exceptions import QasmError
from qbraid.transpiler.annotations import weight

cirq_qasm_import = LazyLoader("cirq_contrib", globals(), "cirq.contrib.qasm_import")
cirq_qasm_parser = LazyLoader("cirq_qasm_parser", globals(), "cirq.contrib.qasm_import._parser")

if TYPE_CHECKING:
    import cirq

    from qbraid.programs.typer import Qasm3StringType


# Gate aliases that Cirq's built-in QASM parser does not recognize, mapped to
# their Cirq-supported equivalents.
_GATE_ALIASES = {
    "cnot": "cx",
    "si": "sdg",
    "ti": "tdg",
    "v": "sx",
    "vi": "sxdg",
    "phaseshift": "p",
    "cphaseshift": "cp",
}


def _merge_terminal_register_measurements(
    circuit: cirq.Circuit, register_sizes: dict[str, int]
) -> cirq.Circuit:
    """Keep complete QASM 3 bit registers together in the Cirq readout.

    Cirq imports ``bit[n] c`` as independent keys ``c_0`` through ``c_(n-1)``. Its QASM 2
    exporter then declares one classical register per key, which loses joint counts on
    backends that report results per register. Only complete terminal registers are
    coalesced. Mid-circuit readout and partial registers keep their original keys.
    """
    import cirq  # pylint: disable=import-outside-toplevel

    indexed_operations = [
        (moment_index, operation)
        for moment_index, moment in enumerate(circuit)
        for operation in moment.operations
    ]
    if sum(isinstance(op.gate, cirq.MeasurementGate) for _, op in indexed_operations) < 2:
        return circuit
    if not any(size > 1 for size in register_sizes.values()):
        return circuit

    # Changing measurement keys would invalidate later classical conditions.
    if any(isinstance(op, cirq.ClassicallyControlledOperation) for _, op in indexed_operations):
        return circuit

    last_on_qubit = {
        qubit: operation for _, operation in indexed_operations for qubit in operation.qubits
    }
    selected: set[tuple[int, cirq.Operation]] = set()
    merged: list[cirq.Operation] = []
    for name, size in register_sizes.items():
        if size < 2:
            continue
        keys = {f"{name}_{index}" for index in range(size)}
        matches = [
            (moment_index, operation)
            for moment_index, operation in indexed_operations
            if isinstance(operation.gate, cirq.MeasurementGate) and operation.gate.key in keys
        ]
        if len(matches) != size or len({op.gate.key for _, op in matches}) != size:
            continue
        if any(
            len(op.qubits) != 1 or last_on_qubit[op.qubits[0]] is not op or op.gate.confusion_map
            for _, op in matches
        ):
            continue
        if any(
            isinstance(op.gate, cirq.MeasurementGate) and op.gate.key == name
            for _, op in indexed_operations
        ):
            continue

        matches_by_key = {op.gate.key: (moment_index, op) for moment_index, op in matches}
        ordered = [matches_by_key[f"{name}_{index}"] for index in range(size)]
        qubits = [op.qubits[0] for _, op in ordered]
        invert_mask = tuple(
            bool(op.gate.invert_mask and op.gate.invert_mask[0]) for _, op in ordered
        )
        merged.append(cirq.MeasurementGate(size, key=name, invert_mask=invert_mask).on(*qubits))
        selected.update(matches)

    if not merged:
        return circuit
    remaining = [
        cirq.Moment(op for op in moment.operations if (index, op) not in selected)
        for index, moment in enumerate(circuit)
    ]
    return cirq.Circuit([*remaining, cirq.Moment(merged)])


@weight(1)
def qasm3_to_cirq(qasm: Qasm3StringType) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input OpenQASM 3 string.

    Cirq's built-in importer handles most OpenQASM 2/3 directly, including
    single-line conditionals. When it cannot, the program is normalized into a
    form Cirq accepts -- gate aliases renamed, custom gates unrolled, barriers
    removed, and QASM 3 braced ``if`` blocks rewritten to single-line syntax --
    and parsing is retried.

    Args:
        qasm: OpenQASM 3 string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input OpenQASM 3 string.
    """
    try:
        parsed = cirq_qasm_parser.QasmParser().parse(qasm)
    except cirq_qasm_import.QasmException:
        try:
            qasm = replace_gate_names(qasm, _GATE_ALIASES)
            qasm_module = pyqasm.loads(qasm)
            qasm_module.unroll()
            if qasm_module.has_barriers():
                logger.warning(
                    "Barriers are not supported in Cirq, "
                    "and will be removed during program conversion."
                )
                qasm_module.remove_barriers()
            qasm = normalize_if_blocks(pyqasm.dumps(qasm_module))
            parsed = cirq_qasm_parser.QasmParser().parse(qasm)
        except cirq_qasm_import.QasmException as err:
            raise QasmError(err) from err
    return _merge_terminal_register_measurements(parsed.circuit, parsed.cregs)
