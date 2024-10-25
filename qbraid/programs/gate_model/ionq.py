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

from enum import Enum
from typing import Any

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import IonQDict

from ._model import GateModelProgram

IONQ_QIS_GATES = [
    "x",
    "y",
    "z",
    "rx",
    "ry",
    "rz",
    "h",
    "cx",
    "s",
    "sdg",
    "t",
    "tdg",
    "sx",
    "sxdg",
    "swap",
]

IONQ_NATIVE_GATES_BASE = ["gpi", "gpi2"]

IONQ_NATIVE_GATES_FAMILY = {
    "aria": ["ms"] + IONQ_NATIVE_GATES_BASE,
    "forte": ["zz"] + IONQ_NATIVE_GATES_BASE,
}

IONQ_NATIVE_GATES = list(set().union(*IONQ_NATIVE_GATES_FAMILY.values()))


class GateSet(Enum):
    """Enumeration of IonQ gate sets types, native and qis (abstract)."""

    NATIVE = "native"
    QIS = "qis"


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
        first_gate_native = circuit[0].get("gate") in native_gate_set

        for instr in circuit:
            gate = instr.get("gate")
            is_native = gate in native_gate_set

            if is_native != first_gate_native:
                raise ValueError(
                    f"Invalid gate '{gate}'. Cannot mix native and QIS gates in the same circuit."
                )

        return GateSet.NATIVE if first_gate_native else GateSet.QIS
