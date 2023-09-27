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
Module for generate random quantum circuits used for testing

"""
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import cirq
import numpy as np

from qbraid._qprogram import QPROGRAM, QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError, QbraidError

QROGRAM_TEST_TYPE = Tuple[Dict[str, Callable[[Any], QPROGRAM]], np.ndarray]

if TYPE_CHECKING:
    import qbraid


def _cirq_random(num_qubits: int, depth: int, **kwargs) -> cirq.Circuit:
    """Generate random circuit of arbitrary size and form.

    Args:
        num_qubits (int): number of quantum wires
        depth (int): layers of operations (i.e. critical path length)

    Raises:
        QbraidError: When invalid cirq random circuit options given

    Returns:
        Cirq random circuit

    """
    if "random_state" not in kwargs:
        kwargs["random_state"] = np.random.randint(1, 11)

    if "op_density" not in kwargs:
        kwargs["op_density"] = 1

    try:
        return cirq.testing.random_circuit(num_qubits, n_moments=depth, **kwargs)
    except ValueError as err:
        raise QbraidError("Could not create Cirq random circuit") from err


def random_circuit(
    package: str, num_qubits: Optional[int] = None, depth: Optional[int] = None, **kwargs
) -> "qbraid.QPROGRAM":
    """Generate random circuit of arbitrary size and form.

    Args:
        package: qBraid supported software package
        num_qubits: Number of quantum wires. If not provided, set randomly in range [2,4].
        depth: Layers of operations (i.e. critical path length)
            If not provided, set randomly in range [2,4].

    Raises:
        PackageValueError: if ``package`` is not supported
        QbraidError: when invalid random circuit options given

    Returns:
        :data:`~qbraid.QPROGRAM`: randomly generated quantum circuit/program

    """
    # todo: custom random gate
    if package not in QPROGRAM_LIBS:
        raise PackageValueError(package)
    num_qubits = np.random.randint(1, 4) if num_qubits is None else num_qubits
    depth = np.random.randint(1, 4) if depth is None else depth
    # pylint: disable=import-outside-toplevel
    if package == "qasm3":
        from qbraid.interface.qbraid_qasm3.random_circuit import _qasm3_random

        rand_circuit = _qasm3_random(num_qubits, depth, **kwargs)
    elif package == "qiskit":
        from qbraid.interface.qbraid_qiskit.random_circuit import _qiskit_random

        rand_circuit = _qiskit_random(num_qubits, depth, **kwargs)
    else:
        rand_circuit = _cirq_random(num_qubits, depth, **kwargs)

        if package != "cirq":
            from qbraid import circuit_wrapper

            qbraid_program = circuit_wrapper(rand_circuit)
            rand_circuit = qbraid_program.transpile(package)

    return rand_circuit


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
