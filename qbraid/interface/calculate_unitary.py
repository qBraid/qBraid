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
Module for calculating unitary of quantum circuit/program

"""
from typing import TYPE_CHECKING, Any, Callable, Optional

import numpy as np
from cirq.testing import assert_allclose_up_to_global_phase

from qbraid.exceptions import ProgramTypeError, QasmError, QbraidError
from qbraid.interface.convert_to_contiguous import convert_to_contiguous
from qbraid.qasm_checks import get_qasm_version

if TYPE_CHECKING:
    import qbraid


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def rev_qubits_unitary(matrix: np.ndarray) -> np.ndarray:
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


def to_unitary(program: "qbraid.QPROGRAM", ensure_contiguous: Optional[bool] = False) -> np.ndarray:
    """Calculates the unitary of any valid input quantum program.

    Args:
        program (:data:`~qbraid.QPROGRAM`): Any quantum program object supported by qBraid.
        ensure_contiguous: If True, calculates unitary using contiguous qubit indexing

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        UnitaryCalculationError: If the programs unitary could not be calculated.

    Returns:
        Matrix representation of the input quantum program.
    """
    to_unitary_function: Callable[[Any], np.ndarray]

    if isinstance(program, str):
        try:
            package = get_qasm_version(program)
        except QasmError as err:
            raise ProgramTypeError(
                "Input of type string must represent a valid OpenQASM program."
            ) from err
    else:
        try:
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    # whether calculated unitary requires permutation
    # to match qBraid qubit ordering convention
    permute = False

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.tools import _unitary_from_qiskit

        permute = True
        to_unitary_function = _unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _unitary_from_cirq

        to_unitary_function = _unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _unitary_from_braket

        to_unitary_function = _unitary_from_braket

    elif "pyquil" in package:
        from qbraid.interface.qbraid_pyquil.tools import _unitary_from_pyquil

        permute = True
        to_unitary_function = _unitary_from_pyquil
    elif "pytket" in package:
        from qbraid.interface.qbraid_pytket.tools import _unitary_from_pytket

        to_unitary_function = _unitary_from_pytket
    elif package == "qasm2":
        from qbraid.interface.qbraid_qasm.tools import _unitary_from_qasm

        to_unitary_function = _unitary_from_qasm
    elif package == "qasm3":
        from qbraid.interface.qbraid_qasm3.tools import _unitary_from_qasm3

        permute = True
        to_unitary_function = _unitary_from_qasm3
    else:
        raise ProgramTypeError(program)

    program_input = convert_to_contiguous(program) if ensure_contiguous else program

    try:
        unitary = to_unitary_function(program_input)
        compat_unitary = rev_qubits_unitary(unitary) if permute else unitary
    except Exception as err:
        raise UnitaryCalculationError(
            "Unitary could not be calculated from given quantum program."
        ) from err

    return compat_unitary


def circuits_allclose(
    circuit0: "qbraid.QPROGRAM",
    circuit1: "qbraid.QPROGRAM",
    index_contig: Optional[bool] = True,
    strict_gphase: Optional[bool] = False,
    **kwargs,
) -> bool:
    """Check if quantum program unitaries are equivalent.

    Args:
        circuit0 (:data:`~qbraid.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        stric_gphase: If False, disregards global phase when verifying
            equivalance of the input circuit's unitaries.

    Returns:
        True if the input circuits pass unitary equality check

    """
    unitary0 = to_unitary(circuit0, ensure_contiguous=index_contig)
    unitary1 = to_unitary(circuit1, ensure_contiguous=index_contig)
    if strict_gphase:
        return np.allclose(unitary0, unitary1)
    try:
        atol = kwargs.pop("atol", None) or 1e-7
        assert_allclose_up_to_global_phase(unitary0, unitary1, atol=atol, **kwargs)
    except AssertionError:
        return False
    return True


def unitary_to_little_endian(matrix: np.ndarray) -> np.ndarray:
    """Converts unitary calculated using big-endian system to its
    equivalent form in a little-endian system.

    Args:
        matrix: big-endian unitary

    Raises:
        ValueError: If input matrix is not unitary

    Returns:
        little-endian unitary

    """
    rank = len(matrix)
    if not np.allclose(np.eye(rank), matrix.dot(matrix.T.conj())):
        raise ValueError("Input matrix must be unitary.")
    num_qubits = int(np.log2(rank))
    tensor_be = matrix.reshape([2] * 2 * num_qubits)
    indicies_in = list(reversed(range(num_qubits)))
    indicies_out = [i + num_qubits for i in indicies_in]
    tensor_le = np.einsum(tensor_be, indicies_in + indicies_out)
    return tensor_le.reshape([rank, rank])


def random_unitary_matrix(dim: int) -> np.ndarray:
    """Create a random (complex) unitary matrix of order `dim`

    Args:
        dim: integer square matrix dimension

    Returns:
        random unitary matrix of shape dim x dim
    """
    # Create a random complex matrix of size dim x dim
    matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    # Use the QR decomposition to get a random unitary matrix
    unitary, _ = np.linalg.qr(matrix)
    return unitary
