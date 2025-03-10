# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining IonQProgram Class

"""
from __future__ import annotations

import json
from enum import Enum
from typing import Any

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import IonQDict

from ._model import GateModelProgram

# https://docs.ionq.com/api-reference/v0.3/writing-quantum-programs#supported-gates
IONQ_QIS_GATES = [
    "x",
    "y",
    "z",
    "rx",
    "ry",
    "rz",
    "h",
    "not",
    "cnot",
    "s",
    "si",
    "t",
    "ti",
    "v",
    "vi",
    "swap",
    "cx",
    "cy",
    "cz",
    "crx",
    "cry",
    "crz",
    "ch",
    "ccnot",
    "cs",
    "csi",
    "ct",
    "cti",
    "cv",
    "cvi",
    "id",
    "zz",
]

IONQ_NATIVE_GATES_BASE = ["gpi", "gpi2"]

IONQ_NATIVE_GATES_FAMILY = {
    "aria": ["ms"] + IONQ_NATIVE_GATES_BASE,
    "forte": ["zz"] + IONQ_NATIVE_GATES_BASE,
}

# https://docs.ionq.com/api-reference/v0.3/native-gates-api#gates
IONQ_NATIVE_GATES = list(set().union(*IONQ_NATIVE_GATES_FAMILY.values()))


class GateSet(Enum):
    """Enumeration of IonQ gate sets types, native and qis (abstract)."""

    NATIVE = "native"
    QIS = "qis"


class InputFormat(Enum):
    """Enumeration of IonQ input format types."""

    CIRCUIT = "ionq.circuit.v0"
    QASM = "qasm"
    OPENQASM = "openqasm"
    QUIPPER = "quipper"


class IonQProgram(GateModelProgram):
    """Wrapper class for ``IonQDict`` objects."""

    def __init__(self, program: IonQDict):
        super().__init__(program)
        if not isinstance(program, IonQDict):
            raise ProgramTypeError(message=f"Expected 'IonQDict' object, got '{type(program)}'.")

    @property
    def qubits(self) -> list[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        num_qubits: int = self.program["qubits"]
        return list(range(num_qubits))

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return 0

    @staticmethod
    def determine_gateset(circuit: list[dict[str, Any]]) -> GateSet:
        """Determines the gate set of an IonQ circuit gate list.

        Args:
            circuit (list[dict]): The IonQ circuit to analyze.

        Returns:
            GateSet: The gate set of the circuit.

        Raises:
            ValueError: If the circuit is empty, or mixes native and abstract (qis) gates.
        """
        if not circuit:
            raise ValueError("Circuit is empty. Must contain at least one gate.")

        native_gate_set = set(IONQ_NATIVE_GATES)

        def is_native_gate(gate_info: dict) -> bool:
            """Helper function to determine if a gate is native."""
            gate = gate_info.get("gate")
            if gate == "zz":
                return gate_info.get("angle") is not None
            return gate in native_gate_set

        first_gate_native = is_native_gate(circuit[0])

        for instr in circuit:
            if is_native_gate(instr) != first_gate_native:
                raise ValueError(
                    f"Invalid gate '{instr.get('gate')}'. "
                    "Cannot mix native and QIS gates in the same circuit."
                )

        return GateSet.NATIVE if first_gate_native else GateSet.QIS

    def validate_for_gateset(self) -> None:
        """Validate that the circuit only contains gates from the derived gate set.

        Raises:
            ValueError: If the circuit contains an invalid gate.
        """
        gate_set_map = {
            GateSet.NATIVE: set(IONQ_NATIVE_GATES),
            GateSet.QIS: set(IONQ_QIS_GATES),
        }

        circuit: list[dict[str, Any]] = self.program["circuit"]

        gate_set_name = IonQProgram.determine_gateset(circuit)

        gate_set = gate_set_map[gate_set_name]

        for instr in circuit:
            gate = instr.get("gate")
            if gate not in gate_set:
                raise ValueError(
                    f"Invalid gate '{gate}'. Must be in the '{gate_set_name.value}' gate set."
                )

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        return {"ionqCircuit": json.dumps(self.program)}
