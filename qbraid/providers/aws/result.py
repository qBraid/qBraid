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
Module defining BraketGateModelResult Class

"""
import numpy as np

from qbraid.providers.result import QuantumJobResult


class BraketGateModelResult(QuantumJobResult):
    """Wrapper class for Amazon Braket result objects."""

    def measurements(self):
        """2d array - row is shot and column is qubit. Default is None. Only available when
        shots > 0. The qubits in `measurements` are the ones in
        `GateModelQuantumTaskResult.measured_qubits`.

        TODO: Make doc-string consistent with parent.

        """
        return np.flip(self._result.measurements, 1)

    def raw_counts(self):
        """Returns the histogram data of the run"""
        braket_counts = dict(self._result.measurement_counts)
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]
        return qbraid_counts
