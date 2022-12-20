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
Module defining CirqResultWrapper Class

"""
import numpy as np

from qbraid.devices.result import ResultWrapper


class CirqResultWrapper(ResultWrapper):
    """Cirq ``Result`` wrapper class."""

    def measurements(self):
        """Return measurements as list"""
        cirq_meas = self.vendor_rlo.measurements
        marray = np.array([cirq_meas[key].flatten() for key in cirq_meas], dtype="int64")
        qbraid_meas = np.einsum("ji->ij", marray)
        return np.flip(qbraid_meas, 1)

    def measurement_counts(self):
        """Returns the histogram data of the run"""
        keys = list(self.vendor_rlo.measurements.keys())
        cirq_counts = dict(self.vendor_rlo.multi_measurement_histogram(keys=keys))
        qbraid_counts = {}
        for key in cirq_counts:
            str_key = "".join(reversed([str(i) for i in key]))
            qbraid_counts[str_key] = cirq_counts[key]
        return qbraid_counts
