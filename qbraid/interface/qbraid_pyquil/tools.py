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

    n = int(np.log2(matrix.shape[0]))
    permuted_matrix = matrix.copy()

    for k in range(n):
        block_size = 2 ** (k + 1)
        for i in range(0, 2**n, block_size):
            for j in range(0, 2**n, block_size):
                (
                    permuted_matrix[i : i + block_size // 2, j : j + block_size // 2],
                    permuted_matrix[
                        i + block_size // 2 : i + block_size, j + block_size // 2 : j + block_size
                    ],
                ) = (
                    matrix[
                        i + block_size // 2 : i + block_size, j + block_size // 2 : j + block_size
                    ].copy(),
                    matrix[i : i + block_size // 2, j : j + block_size // 2].copy(),
                )

    return permuted_matrix


def _unitary_from_pyquil(program: Program) -> np.ndarray:
    """Return the unitary of a pyQuil program."""
    n_qubits = len(program.get_qubits())
    unitary = program_unitary(program, n_qubits=n_qubits)
    return kronecker_product_factor_permutation(unitary)
