# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=invalid-name


"""
Module defining CirqCircuit Class

"""

from cirq.circuits import Circuit

from qbraid.transpiler.programs.abc_qprogram import QuantumProgram


class CirqCircuit(QuantumProgram):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, circuit: Circuit):
        """Create a CirqCircuit

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped

        """
        super().__init__(circuit)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(Circuit(circuit.all_operations()))
        self._package = "cirq"
        self._program_type = "Circuit"
