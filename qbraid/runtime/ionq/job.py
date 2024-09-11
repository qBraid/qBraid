# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=invalid-name

"""
Module defining IonQ job class

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.runtime.enums import ExperimentType, JobStatus
from qbraid.runtime.exceptions import QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import ExperimentalResult, ResultFormatter, RuntimeJobResult

if TYPE_CHECKING:
    import qbraid.runtime.ionq.provider


class IonQJobError(QbraidRuntimeError):
    """Class for errors raised while processing an IonQ job."""


class IonQJob(QuantumJob):
    """IonQ job class."""

    def __init__(self, job_id: str, session: qbraid.runtime.ionq.provider.IonQSession, **kwargs):
        super().__init__(job_id=job_id, **kwargs)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.ionq.provider.IonQSession:
        """Return the IonQ session."""
        return self._session

    def status(self) -> JobStatus:
        """Return the current status of the IonQ job."""
        job_data = self.session.get_job(self.id)
        status = job_data.get("status")

        status_map = {
            "submitted": JobStatus.INITIALIZING,
            "ready": JobStatus.QUEUED,
            "running": JobStatus.RUNNING,
            "failed": JobStatus.FAILED,
            "canceled": JobStatus.CANCELLED,
            "completed": JobStatus.COMPLETED,
        }
        return status_map.get(status, JobStatus.UNKNOWN)

    def cancel(self) -> None:
        """Cancel the IonQ job."""
        self.session.cancel_job(self.id)

    def _build_runtime_gate_model_results(self, job_data, **kwargs):
        """Build the runtime results for a gate model experiment of IONQ."""

        # build state count dict
        state_counts = {}
        shots = job_data.get("shots")
        probs_int = job_data.get("probabilities")
        if shots and probs_int:
            probs_binary = {bin(int(key))[2:].zfill(2): value for key, value in probs_int.items()}
            probs_normal = ResultFormatter.normalize_bit_lengths(probs_binary)
            state_counts = {state: int(prob * shots) for state, prob in probs_normal.items()}

        # build measurements
        measurements = ResultFormatter.counts_to_measurements(state_counts)

        return ExperimentalResult(
            measurements=measurements,
            state_counts=state_counts,
            result_type=ExperimentType.GATE_MODEL,
            execution_duration=job_data.get("execution_time"),
            metadata=job_data,
        )

    def result(self) -> dict:
        """Return the result of the IonQ job."""
        self.wait_for_final_state()
        job_data = self.session.get_job(self.id)
        success = job_data.get("status") == "completed"
        if not success:
            failure = job_data.get("failure", {})
            code = failure.get("code")
            message = failure.get("error")
            raise IonQJobError(f"Job failed with code {code}: {message}")

        results_url = job_data.get("results_url")
        results_endpoint = results_url.split("v0.3")[-1]
        job_data["probabilities"] = self.session.get(results_endpoint).json()
        job_data["shots"] = job_data.get("shots", self._cache_metadata.get("shots"))

        experiments = [self.build_runtime_result(ExperimentType.GATE_MODEL, job_data)]

        return RuntimeJobResult(
            job_id=self.id,
            device_id=job_data.get("target"),
            results=experiments,
            success=success,
        )
