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
Module defining GateModelProgram Class
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from qbraid.programs.program import QuantumProgram

if TYPE_CHECKING:
    import qbraid.runtime


class GateModelProgram(QuantumProgram, ABC):
    """Abstract class for qbraid program wrapper objects."""

    @property
    @abstractmethod
    def qubits(self) -> list[Any]:
        """Return the qubits acted upon by the operations in this circuit."""

    @property
    @abstractmethod
    def num_clbits(self) -> Optional[int]:
        """Return the number of classical bits in the circuit."""

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return len(self.qubits)

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        raise NotImplementedError

    def _unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        raise NotImplementedError

    def unitary(self) -> np.ndarray:
        """Calculate unitary of circuit."""
        if self.spec.alias in ["pyquil", "qiskit", "qasm3"]:
            return self.unitary_rev_qubits()
        return self._unitary()

    def unitary_rev_qubits(self) -> np.ndarray:
        """Performs Kronecker (tensor) product factor permutation of the given matrix.
        Returns a matrix equivalent to that computed from a quantum circuit if its
        qubit indices were reversed.
        """
        matrix = self._unitary()
        if matrix.shape[0] != matrix.shape[1] or (matrix.shape[0] & (matrix.shape[0] - 1)) != 0:
            raise ValueError("Input matrix must be a square matrix of size 2^N for some integer N.")

        num_qubits = int(np.log2(matrix.shape[0]))
        permuted_matrix = np.zeros((2**num_qubits, 2**num_qubits), dtype=complex)

        for i in range(2**num_qubits):
            for j in range(2**num_qubits):
                bits_i = [((i >> bit) & 1) for bit in range(num_qubits)]
                bits_j = [((j >> bit) & 1) for bit in range(num_qubits)]
                reversed_i = sum([bit << (num_qubits - 1 - k) for k, bit in enumerate(bits_i)])
                reversed_j = sum([bit << (num_qubits - 1 - k) for k, bit in enumerate(bits_j)])
                permuted_matrix[reversed_i, reversed_j] = matrix[i, j]

        return permuted_matrix

    def unitary_little_endian(self) -> np.ndarray:
        """Converts unitary calculated using big-endian system to its
        equivalent form in a little-endian system.
        """
        matrix = self.unitary()
        rank = len(matrix)
        if not np.allclose(np.eye(rank), matrix.dot(matrix.T.conj())):
            raise ValueError("Input matrix must be unitary.")
        num_qubits = int(np.log2(rank))
        tensor_be = matrix.reshape([2] * 2 * num_qubits)
        indicies_in = list(reversed(range(num_qubits)))
        indicies_out = [i + num_qubits for i in indicies_in]
        tensor_le = np.einsum(tensor_be, indicies_in + indicies_out)
        return tensor_le.reshape([rank, rank])

    def remove_idle_qubits(self) -> None:
        """Remove empty registers of circuit."""
        raise NotImplementedError

    def reverse_qubit_order(self) -> None:
        """Reverse qubit ordering of circuit."""
        raise NotImplementedError

    def transform(self, device: qbraid.runtime.QuantumDevice) -> None:
        """Transform program according to the device target profile."""
        return None

    def serialize(self) -> dict[str, str]:
        """Return the program in a format suitable for submission to the qBraid API."""
        raise NotImplementedError

    @abstractmethod
    def draw(self, **kwargs) -> Any:
        """Draw the circuit diagram using the appropriate package's method.

        Subclasses must override this to call their native drawing functionality.
        """
        pass
