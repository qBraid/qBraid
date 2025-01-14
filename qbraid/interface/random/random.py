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

from typing import TYPE_CHECKING, Optional

import numpy as np

from qbraid._logging import logger
from qbraid.exceptions import QbraidError
from qbraid.programs.exceptions import PackageValueError
from qbraid.programs.registry import QPROGRAM_ALIASES
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.graph import ConversionGraph

if TYPE_CHECKING:
    import qbraid.programs


def random_circuit(
    package: str,
    num_qubits: Optional[int] = None,
    depth: Optional[int] = None,
    graph: Optional[ConversionGraph] = None,
    max_attempts: int = 1,
    **kwargs,
) -> qbraid.programs.QPROGRAM:
    """Generate random circuit of arbitrary size and form.

    Args:
        package (str): qBraid supported software package
        num_qubits (int, optional): Number of quantum wires.
            If not provided, set randomly in range [1,4].
        depth (int, optional): Layers of operations (i.e. critical path length)
            If not provided, set randomly in range [1,4].
        graph (ConversionGraph, optional): Conversion graph to use for transpilation
        max_attempts (int, optional): Maximum number of attempts to generate a random circuit
        **kwargs: Additional keyword arguments to pass to the random circuit generator

    Raises:
        PackageValueError: if ``package`` is not supported
        ValueError: when no conversion path exists for the specified package
        QbraidError: when random circuit generation fails for the specified package

    Returns:
        qbraid.programs.QPROGRAM: randomly generated quantum circuit/program
    """

    def validate_and_assign(value: Optional[int], name: str):
        if value is None:
            return np.random.randint(1, 4)
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Invalid random circuit option. '{name}' must be a positive integer.")
        return value

    if package not in QPROGRAM_ALIASES:
        raise PackageValueError(f"Package '{package}' is not supported.")

    generator_funcs = {
        "ionq": "qbraid.interface.random.ionq_random.ionq_random",
        "qasm3": "qbraid.interface.random.qasm3_random.qasm3_random",
        "qiskit": "qbraid.interface.random.qiskit_random.qiskit_random",
        "cirq": "qbraid.interface.random.cirq_random.cirq_random",
    }
    graph = graph or ConversionGraph()
    valid_generators = [gen for gen in list(generator_funcs.keys()) if graph.has_path(gen, package)]

    if not valid_generators:
        raise ValueError(
            f"No registered generator that can create a random circuit for '{package}'."
        )

    num_qubits = validate_and_assign(num_qubits, "num_qubits")
    depth = validate_and_assign(depth, "depth")

    sorted_generators = graph.get_sorted_closest_sources(package, valid_generators)

    for src_pkg in sorted_generators:
        func_path = generator_funcs[src_pkg]
        try:
            module_name, func_name = func_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[func_name])
            rand_circuit_func = getattr(module, func_name)

            for attempt in range(max_attempts):
                try:
                    rand_circuit = rand_circuit_func(num_qubits, depth, **kwargs)
                    return transpile(rand_circuit, package)
                except Exception as attempt_err:  # pylint: disable=broad-exception-caught
                    if attempt < max_attempts - 1:
                        logger.info("Attempt %d failed: %s. Retrying...", attempt + 1, attempt_err)
                        continue
                    raise
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.info("Failed to generate circuit with %s: %s", src_pkg, err)
            continue

    raise QbraidError(f"Failed to generate random circuit for program type '{package}'.")


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
