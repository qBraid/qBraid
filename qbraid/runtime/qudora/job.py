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
Module defining QUDORA job class

"""
from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any, Optional

from qbraid_core._import import LazyLoader

from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData, MeasCount

if TYPE_CHECKING:
    import qbraid.runtime.qudora

qbraid_rt_qudora: qbraid.runtime.qudora = LazyLoader(
    "qbraid_rt_qudora", globals(), "qbraid.runtime.qudora"
)


class QUDORARuntimeError(QbraidRuntimeError):
    """Class for errors raised while processing a QUDORA job."""


class QUDORAJob(QuantumJob):
    """QUDORA job class."""

    def __init__(
        self, job_id: int, session: Optional[qbraid.runtime.qudora.QUDORASession] = None, **kwargs
    ):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session or qbraid_rt_qudora.QUDORASession()

    @property
    def session(self) -> qbraid.runtime.qudora.QUDORASession:
        """Return the QUDORA session."""
        return self._session

    @staticmethod
    def _map_status(status: str) -> JobStatus:
        """Convert QUDORA job status to qBraid job status."""
        status_map = {
            "Submitted": JobStatus.INITIALIZING,
            "Uncompiled": JobStatus.QUEUED,
            "Running": JobStatus.RUNNING,
            "Completed": JobStatus.COMPLETED,
            "Cancelling": JobStatus.CANCELLING,
            "Canceled": JobStatus.CANCELLED,
            "Failed": JobStatus.FAILED,
            "Deleted": JobStatus.UNKNOWN,
        }

        return status_map.get(status, JobStatus.UNKNOWN)

    def status(self) -> JobStatus:
        """Return the current status of the QUDORA job."""
        job_data = self.session.get_job(self.id)
        status = job_data.get("status")
        return self._map_status(status)

    def metadata(self) -> dict[str, Any]:
        """Store and return the metadata of the QUDORA job."""
        if self.is_terminal_state() and "status" in self._cache_metadata:
            return self._cache_metadata

        job_metadata = self.session.get_job(self.id)
        cached_backend_settings = self._cache_metadata.get("backend_settings")
        self._cache_metadata.update(job_metadata)
        if (
            cached_backend_settings is not None
            and self._cache_metadata.get("backend_settings") is None
        ):
            self._cache_metadata.update({"backend_settings": cached_backend_settings})

        self._cache_metadata["status"] = self._map_status(self._cache_metadata["status"])
        return self._cache_metadata

    def cancel(self) -> None:
        """Cancel the QUDORA job."""
        self.session.cancel_job(self.id)

    def result(self) -> Result:
        """Return the result of the QUDORA job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id)
        status = self._map_status(job_data["status"])
        success = status == JobStatus.COMPLETED
        if not success:
            message = job_data["user_error"]
            raise QUDORARuntimeError(f"Job finished with status {status.name}: \n \t {message}")

        counts: MeasCount = [ast.literal_eval(count) for count in job_data["result"]]
        data = GateModelResultData(measurement_counts=counts)
        job_id = job_data.pop("job_id", self.id)
        return Result(
            device_id=job_data["target"], job_id=job_id, success=success, data=data, **job_data
        )
