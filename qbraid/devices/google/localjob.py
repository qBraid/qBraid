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
Module defining CirqLocalJobWrapper Class

"""
from datetime import datetime

from qbraid.devices.google.result import CirqResultWrapper
from qbraid.devices.localjob import LocalJobWrapper


class CirqLocalJobWrapper(LocalJobWrapper):
    """CirqLocalJobWrapper class.

    NOTE: This is a place-holder job class for consistency. In Cirq, calling the run method
    on a simulator returns a result object. However, for consistency with the job-like interfaces
    in AWS Braket and IBM Qiskit, we provide this place-holder job class so that run-time is
    procedure is identical for all devices.

    """

    def __init__(self, device, vendor_rlo):
        """Create a CirqSimulatorJob."""

        super().__init__(device, vendor_rlo)
        self.vendor_rlo = vendor_rlo
        self._id = str(self.vendor_rlo).replace(" ", "") + str(datetime.now()).split(" ")[1]

    @property
    def id(self):
        """Return a unique id identifying the job."""
        return self._id

    def metadata(self):
        """Return the metadata regarding the job."""
        return None

    def result(self):
        """Return the results of the job."""
        return CirqResultWrapper(self.vendor_rlo)
