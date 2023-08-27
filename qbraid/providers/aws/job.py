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
Module defining AwsQuantumtaskWrapper Class

"""
import logging

from braket.aws import AwsQuantumTask

from qbraid.providers.enums import JOB_FINAL
from qbraid.providers.exceptions import JobStateError
from qbraid.providers.job import JobLikeWrapper

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
        return self.vendor_jlo.state()

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
