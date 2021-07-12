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

from cirq_google.engine.engine_job import EngineJob
from ..job import JobLikeWrapper


class CirqEngineJobWrapper(JobLikeWrapper):
    def __init__(self, engine_job: EngineJob):
        """Cirq ``EngineJob`` wrapper class.
        Args:
            engine_job (EngineJob): a Cirq ``EngineJob`` object used to run circuits.
        """
        super().__init__(engine_job)

    @property
    def id(self):
        """Return the unique ID of the job within the parent program."""
        return self.vendor_jlo.job_id

    def metadata(self):
        """Returns the labels of the job."""
        return self.vendor_jlo.labels()

    def result(self):
        """Returns the job results, blocking until the job is complete."""
        return self.vendor_jlo.results()

    def status(self):
        """Return the execution status of the job."""
        return self.vendor_jlo.status()

    def cancel(self):
        """Cancel the job."""
        self.vendor_jlo.cancel()
