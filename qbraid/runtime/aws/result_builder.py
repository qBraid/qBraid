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
Module defining BraketGateModelResultBuilder Class

"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Optional

import numpy as np

from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.result_data import AhsShotResult

if TYPE_CHECKING:
    from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
        AnalogHamiltonianSimulationQuantumTaskResult,
    )
    from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult


class ResultDecodingError(QbraidRuntimeError):
    """Exception raised for errors that occur during the decoding of result data."""


class BraketGateModelResultBuilder:
    """Wrapper class for Amazon Braket result objects."""

    def __init__(
        self,
        result: GateModelQuantumTaskResult,
        partial_measurement_qubits: Optional[list[int]] = None,
    ):
        """
        Result builder with partial measurement support.

        Args:
            result: The Braket quantum task result containing measurement data.
            partial_measurement_qubits: Optional list of indices indicating which qubits
                in the measurement results correspond to the original
                partial measurements. If None, all measurements are used.
        """
        self._result = result
        self.partial_measurement_qubits = partial_measurement_qubits

    def measurements(self) -> np.ndarray:
        """
        Get measurement results as a 2D array with partial measurement support.

        Returns a 2D array where each row represents a shot and each column represents
        a qubit measurement result. If partial measurements were used, only the results
        for the originally measured qubits are returned.

        Returns:
            2D numpy array of measurement results. If partial measurements were used,
            the array is filtered to include only the originally measured qubits.
            The qubit order is reversed to match qBraid conventions.
        """
        result: GateModelQuantumTaskResult = self._result
        measurements = result.measurements

        if self.partial_measurement_qubits:
            measurements = marginal_measurement(measurements, self.partial_measurement_qubits)

        # Reverse qubit order to match qBraid conventions
        return np.flip(measurements, 1)

    def get_counts(self) -> dict[str, int]:
        """
        Get measurement counts histogram with partial measurement support.

        Returns:
            Dictionary mapping bitstrings (e.g., "101") to their counts. The bitstring
            order is reversed to match qBraid conventions. If partial measurements were
            used, only the counts for the originally measured qubits are returned.
        """
        result: GateModelQuantumTaskResult = self._result
        braket_counts = dict(result.measurement_counts)

        # Tracing out qubits if partial measurement qubits is specified
        if self.partial_measurement_qubits:
            braket_counts = marginal_count(braket_counts, self.partial_measurement_qubits)

        # Convert to qBraid format with reversed bitstring order
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]
        return qbraid_counts


class BraketAhsResultBuilder:
    """Result from an Analog Hamiltonian Simulation (AHS)."""

    def __init__(
        self,
        result: AnalogHamiltonianSimulationQuantumTaskResult,
        partial_measurement_qubits: Optional[list[int]] = None,
    ):
        """
        AHS result builder.

        Args:
            result: The Braket AHS quantum task result containing measurement data.
            partial_measurement_qubits: Optional list of partial measurement qubit indices.
                Currently not used for AHS results but maintained for interface consistency.
        """
        self._result = result
        self.partial_measurement_qubits = partial_measurement_qubits

    def measurements(self) -> list[AhsShotResult]:
        """Get the list of shot results from the AHS job."""
        result: AnalogHamiltonianSimulationQuantumTaskResult = self._result
        return [
            AhsShotResult(
                success=m.status.name == "SUCCESS",
                pre_sequence=m.pre_sequence,
                post_sequence=m.post_sequence,
            )
            for m in result.measurements
        ]

    def get_counts(self) -> Optional[dict[str, int]]:
        """
        Aggregate state counts from AHS shot results.

        This function decodes the state of atoms at different sites based on
        pre- and post-measurement sequences. Each atom can be in one of three states:
        empty site ('e'), Rydberg state ('r'), or ground state ('g').

        Returns:
            Optional[dict[str, int]]: A dictionary mapping each unique state configuration to
                                      the count of its occurrences across all successful shots,
                                      or None if there are no successful measurements.

        Raises:
            ResultDecodingError: If there is an error accessing required attributes from
                the result object.

        """
        state_counts = Counter()
        states = ["e", "r", "g"]
        try:
            for shot in self.measurements():
                if shot.success:
                    pre = shot.pre_sequence
                    post = shot.post_sequence
                    # converting presequence and postsequence measurements to state_idx
                    state_idx = [
                        0 if pre_i == 0 else 1 if post_i == 0 else 2
                        for pre_i, post_i in zip(pre, post)
                    ]
                    state = "".join(states[s_idx] for s_idx in state_idx)
                    state_counts.update([state])
        except AttributeError as err:
            raise ResultDecodingError from err

        return None if not state_counts else dict(state_counts)


def marginal_measurement(
    measurements: list[list[int]], qubit_indices: list[int]
) -> list[list[int]]:
    """
    Extract marginal measurement results for the specified qubits.

    This function filters the measurement results to include only the qubits
    that were originally measured in partial measurement scenarios.

    Args:
        measurements: Raw measurement results from each shot.
            Each inner list contains the measurement result for all qubits.
        qubit_indices: List of qubit indices to keep in the results.
            Index 0 corresponds to the first element in each shot list.

    Returns:
        Filtered measurement results containing only the specified qubits.

    Example:
        >>> measurements = [[0, 1, 0, 1], [1, 0, 1, 0]]
        >>> qubit_indices = [0, 2]
        >>> marginal_measurement(measurements, qubit_indices)
        [[0, 0], [1, 1]]
    """
    return [[shot[i] for i in qubit_indices] for shot in measurements]


def marginal_count(count_dict: dict[str, int], qubit_indices: list[int]) -> dict[str, int]:
    """
    Compute marginal counts for specified qubits from measurement count data.

    This function aggregates measurement counts by summing over the unmeasured qubits,
    effectively marginalizing the probability distribution to include only the
    originally measured qubits in partial measurement scenarios.

    Args:
        count_dict: Dictionary mapping bitstrings to their occurrence counts.
            Keys are bitstrings like "0101", values are integer counts.
        qubit_indices: List of qubit indices to keep in the marginalized results.
            Index 0 corresponds to the leftmost bit in the bitstring.

    Returns:
        Dictionary mapping reduced bitstrings to their marginal counts.

    Example:
        >>> count_dict = {"0101": 10, "0111": 5, "1101": 3}
        >>> qubit_indices = [0, 2]
        >>> marginal_count(count_dict, qubit_indices)
        {"00": 10, "01": 5, "10": 3}
    """
    marginal: dict[str, int] = {}

    for bitstring, count in count_dict.items():
        reduced_bits = "".join(bitstring[i] for i in qubit_indices)
        marginal[reduced_bits] = marginal.get(reduced_bits, 0) + count

    return marginal
