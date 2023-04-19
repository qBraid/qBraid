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
Module defining IBMResultWrapper Class

"""
import numpy as np

from qbraid.devices.result import ResultWrapper


class IBMResultWrapper(ResultWrapper):
    """Qiskit ``Result`` wrapper class."""

    def measurements(self):
        """Return measurements as list"""
        qiskit_meas = self.vendor_rlo.get_memory()
        qbraid_meas = []
        for str_shot in qiskit_meas:
            lst_shot = [int(x) for x in list(str_shot)]
            qbraid_meas.append(lst_shot)
        return np.array(qbraid_meas)

    def measurement_counts(self):
        """Returns the histogram data of the run"""
        return self.vendor_rlo.get_counts()
