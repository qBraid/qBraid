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
Module for generate random quantum circuits used for testing

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

import numpy as np

from qbraid.programs.exceptions import PackageValueError
from qbraid.programs.registry import QPROGRAM, QPROGRAM_ALIASES
from qbraid.transpiler.converter import transpile

QROGRAM_TEST_TYPE = tuple[dict[str, Callable[[Any], QPROGRAM]], np.ndarray]

if TYPE_CHECKING:
    import qbraid.programs


def random_circuit(
    package: str, num_qubits: Optional[int] = None, depth: Optional[int] = None, **kwargs
) -> qbraid.programs.QPROGRAM:
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
        :data:`~qbraid.programs.QPROGRAM`: randomly generated quantum circuit/program

    """
    if package not in QPROGRAM_ALIASES:
        raise PackageValueError(package)

    num_qubits = np.random.randint(1, 4) if num_qubits is None else num_qubits
    depth = np.random.randint(1, 4) if depth is None else depth

    # pylint: disable=import-outside-toplevel
    if package == "qasm3":
        from qbraid.interface.random.qasm3_random import _qasm3_random

        rand_circuit = _qasm3_random(num_qubits, depth, **kwargs)
    elif package == "qiskit":
        from qbraid.interface.random.qiskit_random import _qiskit_random

        rand_circuit = _qiskit_random(num_qubits, depth, **kwargs)
    else:
        from qbraid.interface.random.cirq_random import _cirq_random

        rand_circuit = _cirq_random(num_qubits, depth, **kwargs)

        if package != "cirq":
            rand_circuit = transpile(rand_circuit, package)

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
