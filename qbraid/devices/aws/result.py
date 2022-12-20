# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining BraketResultWrapper Class

"""
import numpy as np

from qbraid.devices.result import ResultWrapper


class BraketResultWrapper(ResultWrapper):
    """Wrapper class for Amazon Braket result objects."""

    def measurements(self):
        """2d array - row is shot and column is qubit. Default is None. Only available when
        shots > 0. The qubits in `measurements` are the ones in
        `GateModelQuantumTaskResult.measured_qubits`.

        TODO: Make doc-string consistent with parent.

        """
        return np.flip(self.vendor_rlo.measurements, 1)

    def measurement_counts(self):
        """Returns the histogram data of the run"""
        braket_counts = dict(self.vendor_rlo.measurement_counts)
        qbraid_counts = {}
        for key in braket_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = braket_counts[key]
        return qbraid_counts

    def data(self):
        """Return the raw data associated with the run/job."""
        try:
            return self.vendor_rlo.data()
        except AttributeError as err:
            raise AttributeError(
                "This method is only available for 'AnnealingQuantumTaskResult' wrapper objects. "
                "Available methods for 'GateModelQuantumTaskResult' wrapper objects include "
                "'measurements' and 'measurement_counts'."
            ) from err
