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
Module defining Qasm2CircuitWrapper Class

"""

from cirq.circuits import Circuit

from qbraid.interface.qbraid_qasm.tools import qasm_num_qubits, qasm_qubits
from qbraid.transpiler.cirq_qasm.qasm_conversions import from_qasm
from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class QasmCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, qasm_str: str):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped

        """
        # coverage: ignore
        super().__init__(qasm_str)

        self._qubits = qasm_qubits(qasm_str)
        self._num_qubits = qasm_num_qubits(qasm_str)
        self._depth = len(Circuit(from_qasm(qasm_str).all_operations()))
        self._package = "openqasm"
        self._program_type = "str"
