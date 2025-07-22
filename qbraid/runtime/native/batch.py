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
Module defining the QbraidBatchJob Class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import qbraid_core

from qbraid.runtime.batch import BatchQuantumJob

from .job import QbraidJob

if TYPE_CHECKING:
    import qbraid.runtime


class QbraidBatchJob(BatchQuantumJob):
    """Qbraid batch job class."""

    def __init__(
        self,
        device: qbraid.runtime.QbraidDevice,
        client: Optional[qbraid_core.services.quantum.QuantumClient] = None,
        max_timeout: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(device, client, max_timeout, **kwargs)

    def fetch_jobs(self) -> None:
        """Fetch the jobs associated with this batch."""
        if self.is_terminal_state():
            return

        jobs = self._fetch_jobs_from_backend()
        self._jobs = [
            # TODO: Is this okay or we need original job objects?
            # most likely we need original job objects here.
            QbraidJob(job_id=job["qbraidJobId"], device=self, client=self.client)
            for job in jobs
        ]

    def aggregate(self):
        """Aggregate the results of the qBraid batch job."""
