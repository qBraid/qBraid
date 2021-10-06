# Copyright 2019 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# NOTICE: This file has been modified from the original:
# https://github.com/quantumlib/Cirq/blob/master/cirq-google/cirq_google/engine/engine_job.py

"""CirqEngineJobWrapper Class"""

from __future__ import annotations

from cirq_google.engine.engine_job import EngineJob

from qbraid.devices.job import JobLikeWrapper


class CirqEngineJobWrapper(JobLikeWrapper):
    """Wrapper class for Google Cirq ``EngineJob`` objects."""

    def __init__(self, device, circuit, vendor_jlo: EngineJob):
        """Create a CirqEngineJobWrapper

        Args:
            device: the CirqEngineDeviceWrapper associated with this job
            circuit: qbraid wrapped circuit object used in this job
            vendor_jlo (EngineJob): a Cirq ``EngineJob`` object used to run circuits.

        """
        super().__init__(device, circuit, vendor_jlo)

    @property
    def vendor_job_id(self) -> str:
        """Return the job ID from the vendor job-like-object."""
        return self.vendor_jlo.job_id

    @property
    def _shots(self) -> int:
        """Return the number of repetitions used in the run"""
        return 0

    def _status(self):
        """Returns status from Cirq Google Engine Job object."""
        return self.vendor_jlo.status()

    def ended_at(self):
        """The time when the job ended."""
        return "TODO"

    def result(self):
        """Returns the job results, blocking until the job is complete."""
        return self.vendor_jlo.results()

    def cancel(self):
        """Cancel the job."""
        self.vendor_jlo.cancel()
