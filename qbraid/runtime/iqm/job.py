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
Module for IQM job class.

"""

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.job import QuantumJob

from .result import IQMJobResult

class IQMJob(QuantumJob):
    """IQM job class."""

    def __init__(self, job_id, **kwargs):
        super().__init__(job_id, **kwargs)

    def status(self) -> JobStatus:
        """Return the status of the job."""
        raise NotImplementedError

    def result(self) -> IQMJobResult:
        """Return the result of the job."""
        raise NotImplementedError
    
    def cancel(self):
        """Cancel the job."""
        raise NotImplementedError