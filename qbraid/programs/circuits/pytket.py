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
Module defining PytketCircuit Class

"""

from typing import Optional, Union

import numpy as np
from pytket.circuit import Circuit, Command, OpType
from pytket.circuit_library import TK1_to_RzRx
from pytket.passes import DecomposeBoxes, RebaseCustom, SafetyMode
from pytket.predicates import (
    CompilationUnit,
    GateSetPredicate,
    MaxNQubitsPredicate,
    NoClassicalControlPredicate,
    NoFastFeedforwardPredicate,
    NoMidMeasurePredicate,
    NoSymbolsPredicate,
)
from pytket.unit_id import Qubit

from qbraid.programs.exceptions import ProgramTypeError, TransformError

from ._model import GateModelProgram

IONQ_GATES = {
    OpType.X,
    OpType.Y,
    OpType.Z,
    OpType.Rx,
    OpType.Ry,
    OpType.Rz,
    OpType.H,
    OpType.CX,
    OpType.S,
    OpType.Sdg,
    OpType.T,
    OpType.Tdg,
    OpType.V,
    OpType.Vdg,
    OpType.Measure,
    OpType.noop,
    OpType.SWAP,
    OpType.ZZPhase,
    OpType.XXPhase,
    OpType.YYPhase,
    OpType.ZZMax,
    OpType.Barrier,
}


class PytketCircuit(GateModelProgram):
    """Wrapper class for ``pytket.circuit.Circuit`` objects."""

    def __init__(self, program: Circuit):
        super().__init__(program)
        if not isinstance(program, Circuit):
            raise ProgramTypeError(
                message=f"Expected 'pytket.Circuit' object, got '{type(program)}'."
            )

    @property
    def qubits(self) -> list[Qubit]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self.program.qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self.program.n_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self.program.n_bits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self.program.depth()

    @staticmethod
    def remove_measurements(original_circuit):
        """
        Return a new circuit with all non-measurement operations from the original circuit.

        Args:
            original_circuit: The pytket Circuit to process.

        Returns:
            A new pytket Circuit without measurement operations.
        """
        new_circuit = Circuit()
        for qreg in original_circuit.qubits:
            new_circuit.add_qubit(qreg)
        for creg in original_circuit.bits:
            new_circuit.add_bit(creg)

        for command in original_circuit.get_commands():
            if command.op.type != OpType.Measure:
                new_circuit.add_gate(
                    command.op.type, command.op.params, [q.index[0] for q in command.qubits]
                )

        return new_circuit

    def _unitary(self) -> np.ndarray:
        """Return the unitary of a pytket circuit."""
        try:
            return self.program.get_unitary()
        except RuntimeError:
            program_copy = self.remove_measurements(self.program)
            return program_copy.get_unitary()

    def remove_idle_qubits(self) -> None:
        """Checks whether the circuit uses contiguous qubits/indices,
        and if not, reduces dimension accordingly."""
        circuit = self.program.copy()
        circuit.remove_blank_wires()
        self._program = circuit

    def reverse_qubit_order(self) -> None:
        """Reverses the qubit ordering of a PyTKET circuit."""
        new_c = Circuit(self.num_qubits)
        for gate in self.program.get_commands():
            circuit_qubits = gate.qubits
            circuit_qubits = [(self.num_qubits - 1) - qubits.index[0] for qubits in circuit_qubits]
            gate_op = gate.op
            # devide parameter by pi, from radian to degree
            new_c.add_gate(
                gate_op.type,
                np.array(gate_op.params) / np.pi if gate_op.params else gate_op.params,
                circuit_qubits,
            )
        self._program = new_c

    @staticmethod
    def gate_to_matrix(
        gates: Optional[Union[list[Circuit], Command]], flat: bool = False
    ) -> np.ndarray:
        """Return the unitary of the Command"""
        gates = gates if (list == type(gates)) else [gates]
        a = list(map(max, [gate.qubits for gate in gates]))
        circuit = Circuit(max(a).index[0] + 1)
        for gate in gates:
            gate_op = gate.op
            circuit.add_gate(gate_op.type, gate_op.params, gate.qubits)
        if flat:
            circuit.remove_blank_wires()
        return circuit.get_unitary()

    @staticmethod
    def rebase(
        circuit: Circuit,
        gates: set[OpType],
        max_qubits: int,
        safety_mode: SafetyMode = SafetyMode.Default,
    ) -> Circuit:
        """
        Rebase a PyTKET circuit according to a given gate set and maximum number of qubits.

        Args:
            circuit (pytket.circuit.Circuit): The input PyTKET circuit to be rebased.

        Returns:
            pytket.circuit.Circuit: The rebased PyTKET circuit.

        """
        preds = [
            NoClassicalControlPredicate(),
            NoFastFeedforwardPredicate(),
            NoMidMeasurePredicate(),
            NoSymbolsPredicate(),
            GateSetPredicate(gates),
            MaxNQubitsPredicate(max_qubits),
        ]

        ionq_rebase_pass = RebaseCustom(
            gateset=gates, cx_replacement=Circuit(), tk1_replacement=TK1_to_RzRx
        )
        cu = CompilationUnit(circuit, preds)
        DecomposeBoxes().apply(cu, safety_mode=safety_mode)
        ionq_rebase_pass.apply(cu, safety_mode=safety_mode)
        try:
            assert cu.check_all_predicates()
        except AssertionError as err:
            raise TransformError(
                "Rebased circuit failed to satisfy compilation predicates"
            ) from err
        return cu.circuit

    def transform(self, device) -> None:
        """Transform program to according to device target profile."""
        num_qubits = device.profile.get("num_qubits")
        provider_name = device.profile.get("provider_name", "").upper()

        if provider_name == "IONQ":
            self._program = self.rebase(self.program, IONQ_GATES, num_qubits)
