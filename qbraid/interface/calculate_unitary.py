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

from qbraid.exceptions import ProgramTypeError, QbraidError
from qbraid.interface.convert_to_contiguous import convert_to_contiguous

if TYPE_CHECKING:
    import qbraid


class UnitaryCalculationError(QbraidError):
    """Exception raised during unitary calculation"""


def to_unitary(program: "qbraid.QPROGRAM", ensure_contiguous: Optional[bool] = False) -> np.ndarray:
    """Calculate the unitary of a quantum program.

    Args:
        program: Quantum program object supported by qBraid.
        ensure_contiguous: Calculate unitary using contiguous qubit indexing if True.

    Raises:
        ProgramTypeError: If the input quantum program is not supported.
        UnitaryCalculationError: If the program's unitary could not be calculated.

    Returns:
        Matrix representation of the input quantum program.
    """
    to_unitary_function: Callable[[Any], np.ndarray]

    if isinstance(program, str):
        package = "qasm"
    else:
        try:
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.tools import _unitary_from_qiskit

        to_unitary_function = _unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _unitary_from_cirq

        to_unitary_function = _unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _unitary_from_braket

        to_unitary_function = _unitary_from_braket

    elif "pyquil" in package:
        from qbraid.interface.qbraid_pyquil.tools import _unitary_from_pyquil

        to_unitary_function = _unitary_from_pyquil
    elif "pytket" in package:
        from qbraid.interface.qbraid_pytket.tools import _unitary_from_pytket

        to_unitary_function = _unitary_from_pytket
    elif "qasm" in package:
        from qbraid.interface.qbraid_qasm.tools import _unitary_from_qasm

        to_unitary_function = _unitary_from_qasm
    else:
        raise ProgramTypeError(program)

    program_input = convert_to_contiguous(program) if ensure_contiguous else program

    try:
        unitary = to_unitary_function(program_input)
    except Exception as err:
        raise UnitaryCalculationError(
            "Unitary could not be calculated from given quantum program."
        ) from err

    return unitary


def circuits_allclose(
    circuit0: "qbraid.QPROGRAM",
    circuit1: "qbraid.QPROGRAM",
    index_contig: Optional[bool] = True,
    strict_gphase: Optional[bool] = False,
    **kwargs,
) -> bool:
    """Check if two quantum programs have equivalent unitaries.

    Args:
        circuit0: First quantum program to compare.
        circuit1: Second quantum program to compare.
        index_contig: Calculate circuit unitaries using contiguous qubit indexing if True.
        strict_gphase: Consider global phase when verifying equivalance if False.

    Returns:
        True if the input circuits pass the unitary equality check.
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
    """Convert a big-endian unitary matrix to little-endian.

    Args:
        matrix: Big-endian unitary matrix.

    Raises:
        ValueError: If the input matrix is not unitary.

    Returns:
        Little-endian unitary matrix.
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
    """Create a random complex unitary matrix of given dimension.

    Args:
        dim: Dimension of the square matrix.

    Returns:
        Random unitary matrix of shape dim x dim.
    """
    # Create a random complex matrix of size dim x dim
    matrix = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    # Use the QR decomposition to get a random unitary matrix
    unitary, _ = np.linalg.qr(matrix)
    return unitary
