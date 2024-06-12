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
from collections import Counter

import numpy as np
from braket.tasks.analog_hamiltonian_simulation_quantum_task_result import (
    AnalogHamiltonianSimulationShotStatus,
    ShotResult,
)

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

    def measurements(self):
        """Get the list of shot results from the AHS job."""
        measurements = []
        for measurement in self._result.measurements:
            status = AnalogHamiltonianSimulationShotStatus(measurement.shotMetadata.shotStatus)
            if measurement.shotResult.preSequence:
                pre_sequence = np.asarray(measurement.shotResult.preSequence, dtype=int)
            else:
                pre_sequence = None
            if measurement.shotResult.postSequence:
                post_sequence = np.asarray(measurement.shotResult.postSequence, dtype=int)
            else:
                post_sequence = None
            measurements.append(ShotResult(status, pre_sequence, post_sequence))
        return measurements

    def get_counts(self) -> dict[str, int]:
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
        state_counts = Counter()
        states = ["e", "r", "g"]
        try:
            for shot in self.measurements():
                if shot.status.name == "SUCCESS":
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
