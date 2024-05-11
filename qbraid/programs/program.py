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
Module defining QuantumProgram Class

"""
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional

import numpy as np

from .alias_manager import get_program_type_alias
from .exceptions import ProgramTypeError
from .registry import QPROGRAM_REGISTRY
from .spec import ProgramSpec

if TYPE_CHECKING:
    import qbraid

logger = logging.getLogger(__name__)


class QuantumProgram(ABC):
    """Abstract class for qbraid program wrapper objects."""

    def __init__(self, program: "qbraid.programs.QPROGRAM"):
        self.spec = self.get_spec(program)
        self._program = None
        self.program = program

    @property
    def program(self) -> "qbraid.programs.QPROGRAM":
        """Return the quantum program."""
        return self._program

    @program.setter
    def program(self, value: "qbraid.programs.QPROGRAM") -> None:
        """Set the quantum program."""
        expected_type = QPROGRAM_REGISTRY.get(self.spec.alias)
        if not isinstance(value, expected_type):
            raise ProgramTypeError(
                message=(
                    f"Expected program type of '{expected_type}' for "
                    f"derived type alias '{self.spec.alias}'."
                )
            )
        self._program = value

    @staticmethod
    def get_spec(program: "qbraid.programs.QPROGRAM") -> ProgramSpec:
        """Return the program spec."""
        try:
            alias = get_program_type_alias(program)
        except ProgramTypeError as err:
            logger.info(err)
            alias = None

        return ProgramSpec(type(program), alias)

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""

    @abstractmethod
    def unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""


class QbraidProgram(QuantumProgram, ABC):
    """Abstract class for qbraid program wrapper objects."""

    @property
    @abstractmethod
    def qubits(self) -> list[Any]:
        """Return the qubits acted upon by the operations in this circuit"""

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return len(self.qubits)

    @property
    @abstractmethod
    def num_clbits(self) -> Optional[int]:
        """Return the number of classical bits in the circuit."""

    @property
    @abstractmethod
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""

    @abstractmethod
    def _unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""

    def unitary(self) -> "np.ndarray":
        """Calculate unitary of circuit."""
        if self.spec.alias in ["pyquil", "qiskit", "qasm3"]:
            return self.unitary_rev_qubits()
        return self._unitary()

    def unitary_rev_qubits(self) -> np.ndarray:
        """Peforms Kronecker (tensor) product factor permutation of given matrix.
        Returns a matrix equivalent to that computed from a quantum circuit if its
        qubit indicies were reversed.

        Args:
            matrix (np.ndarray): The input matrix, assumed to be a 2^N x 2^N square matrix
                                where N is an integer.

        Returns:
            np.ndarray: The matrix with permuted Kronecker product factors.

        Raises:
            ValueError: If the input matrix is not square or its size is not a power of 2.
        """
        matrix = self._unitary()
        if matrix.shape[0] != matrix.shape[1] or (matrix.shape[0] & (matrix.shape[0] - 1)) != 0:
            raise ValueError("Input matrix must be a square matrix of size 2^N for some integer N.")

        # Determine the number of qubits from the matrix size
        num_qubits = int(np.log2(matrix.shape[0]))

        # Create an empty matrix of the same size
        permuted_matrix = np.zeros((2**num_qubits, 2**num_qubits), dtype=complex)

        for i in range(2**num_qubits):
            for j in range(2**num_qubits):
                # pylint: disable=consider-using-generator
                # Convert indices to binary representations (qubit states)
                bits_i = [((i >> bit) & 1) for bit in range(num_qubits)]
                bits_j = [((j >> bit) & 1) for bit in range(num_qubits)]

                # Reverse the bits
                reversed_i = sum([bit << (num_qubits - 1 - k) for k, bit in enumerate(bits_i)])
                reversed_j = sum([bit << (num_qubits - 1 - k) for k, bit in enumerate(bits_j)])

                # Update the new matrix
                permuted_matrix[reversed_i, reversed_j] = matrix[i, j]

        return permuted_matrix

    def unitary_little_endian(self) -> np.ndarray:
        """Converts unitary calculated using big-endian system to its
        equivalent form in a little-endian system.

        Args:
            matrix: big-endian unitary

        Raises:
            ValueError: If input matrix is not unitary

        Returns:
            little-endian unitary

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

    @abstractmethod
    def remove_idle_qubits(self) -> None:
        """Remove empty registers of circuit."""

    @abstractmethod
    def reverse_qubit_order(self) -> None:
        """Rerverse qubit ordering of circuit."""
