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

from qbraid_core.services.quantum import QuantumClient

from qbraid._logging import logger
from qbraid.runtime.batch import BatchQuantumJob
from qbraid.runtime.enums import BatchJobStatus, JobStatus
from qbraid.runtime.exceptions import ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.result_data import ResultDataType


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

    def aggregate(self):
        """Aggregate the results of the qBraid batch job."""
        return super().aggregate()
