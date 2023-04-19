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
Module defining AwsQuantumtaskWrapper Class

"""
import logging

from braket.aws import AwsQuantumTask

from qbraid.devices.enums import JOB_FINAL
from qbraid.devices.exceptions import JobStateError
from qbraid.devices.job import JobLikeWrapper

from .result import AwsGateModelResultWrapper


class AwsQuantumTaskWrapper(JobLikeWrapper):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects."""

    def __init__(self, job_id: str, **kwargs):
        """Create a AwsQuantumTaskWrapper."""

        super().__init__(job_id, **kwargs)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return AwsQuantumTask(self.vendor_job_id)

    def _get_status(self):
        """Returns status from Braket QuantumTask object metadata."""
        return self.vendor_jlo.metadata()["status"]

    def result(self) -> AwsGateModelResultWrapper:
        """Return the results of the job."""
        if self.status() not in JOB_FINAL:
            logging.info("Result will be available when job has reached final state.")
        return AwsGateModelResultWrapper(self.vendor_jlo.result())

    def cancel(self) -> None:
        """Cancel the quantum task."""
        status = self.status()
        if status in JOB_FINAL:
            raise JobStateError(f"Cannot cancel quantum job in the {status} state.")
        return self.vendor_jlo.cancel()
