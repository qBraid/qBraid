# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""
Module containing pyQuil tools

"""
import numpy as np
from pyquil import Program
from pyquil.simulation.tools import program_unitary


def kronecker_product_factor_permutation(matrix: np.ndarray) -> np.ndarray:
    """Permutes the Kronecker (tensor) product factors of the given matrix.
    In other words, this function returns a matrix equivalent to that computed
    from a quantum circuit if its qubit indicies were reversed.

    Args:
        matrix (np.ndarray): The input matrix, assumed to be a 2^N x 2^N square matrix
                             where N is an integer.

    Returns:
        np.ndarray: The matrix with permuted Kronecker product factors.

    Raises:
        ValueError: If the input matrix is not square or its size is not a power of 2.
    """
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


def _unitary_from_pyquil(program: Program) -> np.ndarray:
    """Return the unitary of a pyQuil program."""
    n_qubits = len(program.get_qubits())
    unitary = program_unitary(program, n_qubits=n_qubits)
    return kronecker_product_factor_permutation(unitary)
