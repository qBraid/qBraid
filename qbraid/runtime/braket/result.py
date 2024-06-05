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
Module defining BraketGateModelJobResult Class

"""
from typing import Optional

import numpy as np

from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.result import GateModelJobResult, QuantumJobResult


class ResultDecodingError(QbraidRuntimeError):
    """Exception raised for errors that occur during the decoding of result data."""


class BraketGateModelJobResult(GateModelJobResult):
    """Wrapper class for Amazon Braket result objects."""

    def measurements(self):
        """
        2d array - row is shot and column is qubit. Default is None.
        Only available when shots > 0. The qubits in `measurements` are
        the ones in `GateModelQuantumTaskResult.measured_qubits`.

        """
        return np.flip(self._result.measurements, 1)

    def raw_counts(self, **kwargs):
        """Returns the histogram data of the run"""
        braket_counts = dict(self._result.measurement_counts)
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]
        return qbraid_counts


class BraketAhsJobResult(QuantumJobResult):
    """Result from an Analog Hamiltonian Simulation (AHS)."""

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
            ValueError: If there is an error accessing required attributes within the result object.
        """
        result = self._result

        if not result or not hasattr(result, "measurements") or not result.measurements:
            return None

        state_counts = {}
        states = ["e", "r", "g"]

        def determine_state(pre, post):
            """Determine the state of an atom based on its pre- and post-sequence values."""
            return states[0] if pre == 0 else states[1] if post == 0 else states[2]

        try:
            for shot in result.measurements:
                if shot.status.name == "SUCCESS":
                    state = "".join(
                        determine_state(pre, post)
                        for pre, post in zip(shot.pre_sequence, shot.post_sequence)
                    )
                    state_counts[state] = state_counts.get(state, 0) + 1
        except AttributeError as err:
            raise ResultDecodingError from err

        if not state_counts:
            return None

        return state_counts
