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
Module for transforming Cirq circuits.

"""

from typing import TYPE_CHECKING

from cirq.contrib.qasm_import import circuit_from_qasm

if TYPE_CHECKING:
    import cirq  # type: ignore


def decompose(circuit: "cirq.Circuit", strategy: str = "qasm") -> "cirq.Circuit":
    """
    Flatten a Cirq circuit.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to flatten.
        strategy (str): The decomposition strategy to use. Defaults to 'qasm'.

    Returns:
        cirq.Circuit: The flattened Cirq circuit.

    Raises:
        ValueError: If the decomposition strategy is not supported.

    """
    # TODO: potentially replace with native cirq.decompose
    # https://quantumai.google/reference/python/cirq/decompose

    if strategy == "qasm":
        return circuit_from_qasm(circuit.to_qasm())

    raise ValueError(f"Decomposition strategy '{strategy}' not supported.")
