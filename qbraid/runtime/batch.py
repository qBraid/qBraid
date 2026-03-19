# Copyright 2025 qBraid
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
Module defining BatchJobSession context manager and BatchResult container.

"""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any, Callable, Optional

from qbraid._logging import logger
from qbraid.runtime.result import Result

if TYPE_CHECKING:
    from qbraid_core.services.runtime.schemas import BatchJob, BatchStatus

    from qbraid.runtime.job import QuantumJob


# Thread-safe context variables for tracking active batch
_active_batch: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "_active_batch", default=None
)
_active_batch_session: contextvars.ContextVar[Optional[BatchJobSession]] = contextvars.ContextVar(
    "_active_batch_session", default=None
)


def get_active_batch() -> Optional[str]:
    """Return the batchJobQrn of the currently active batch, or None.

    Called by QuantumDevice.run() to check if jobs should be tagged
    with a batch identifier.
    """
    return _active_batch.get(None)


def get_active_batch_session() -> Optional[BatchJobSession]:
    """Return the active BatchJobSession, or None.

    Called by QbraidDevice.submit() to register jobs
    with the active batch session.
    """
    return _active_batch_session.get(None)


class BatchResult:
    """Container for results of all jobs in a batch.

    Provides dict-like access to individual job results keyed by jobQrn.

    Attributes:
        batch_id: The batchJobQrn identifier.
        results: Mapping of jobQrn -> Result[ResultDataType].

    Example:
        >>> batch_result = batch.results()
        >>> for job_id, result in batch_result.items():
        ...     counts = result.data.get_counts()
        ...     print(f"{job_id}: {counts}")
    """

    def __init__(self, batch_id: str, results: dict[str, Result]):
        self.batch_id = batch_id
        self.results = results

    def __getitem__(self, job_id: str) -> Result:
        """Get result by job QRN."""
        return self.results[job_id]

    def __iter__(self):
        """Iterate over job QRNs."""
        return iter(self.results)

    def __len__(self) -> int:
        """Number of results."""
        return len(self.results)

    def items(self):
        """Iterate over (jobQrn, Result) pairs."""
        return self.results.items()

    def keys(self):
        """Return job QRNs."""
        return self.results.keys()

    def values(self):
        """Return Result objects."""
        return self.results.values()

    def successful(self) -> dict[str, Result]:
        """Return only successful job results."""
        return {k: v for k, v in self.results.items() if v.success}

    def failed(self) -> dict[str, Result]:
        """Return only failed job results."""
        return {k: v for k, v in self.results.items() if not v.success}

    def __repr__(self) -> str:
        """String representation."""
        success = len(self.successful())
        fail = len(self.failed())
        return (
            f"BatchResult(batch_id='{self.batch_id}', "
            f"total={len(self)}, successful={success}, failed={fail})"
        )


class BatchJobSession:
    """Context manager for grouping quantum job submissions into a batch.

    Jobs submitted via any QuantumDevice.run() call within this context
    are automatically tagged with the batch's QRN. The batch supports
    cross-device and cross-provider job submissions.

    Args:
        name: Optional human-readable name for the batch.
        tags: Optional tags for filtering/organizing batches.
        metadata: Optional metadata dict.
        client: Optional QuantumRuntimeClient instance. If not provided,
            a default client is created.

    Example:
        >>> from qbraid.runtime import BatchJobSession
        >>> with BatchJobSession(name="sweep") as batch:
        ...     job1 = device_a.run(circuit_1)
        ...     job2 = device_b.run(circuit_2)
        >>> results = batch.results(timeout=300)
        >>> for job_id, result in results.items():
        ...     print(result.data.get_counts())

    Cross-references:
        - Context variable read by: QbraidDevice.submit() (native/device.py:92-147)
        - Core schemas: qbraid_core.services.runtime.schemas (BatchJob, BatchStatus)
    """

    def __init__(
        self,
        name: Optional[str] = None,
        tags: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        client: Optional[Any] = None,
    ):
        self._name = name
        self._tags = tags or {}
        self._metadata = metadata or {}
        self._client = client
        self._batch_data: Optional[BatchJob] = None
        self._jobs: list[QuantumJob] = []
        self._token: Optional[contextvars.Token] = None
        self._session_token: Optional[contextvars.Token] = None
        self._on_complete_callback: Optional[Callable[[dict[str, Result]], None]] = None
        self._on_complete_timeout: Optional[int] = None
        self._on_complete_poll_interval: float = 5.0

    @property
    def client(self):
        """Lazily initialize the QuantumRuntimeClient."""
        if self._client is None:
            from qbraid_core.services.runtime import QuantumRuntimeClient

            self._client = QuantumRuntimeClient()
        return self._client

    @property
    def batch_id(self) -> Optional[str]:
        """Return the batch QRN, or None if not yet opened."""
        return self._batch_data.batchJobQrn if self._batch_data else None

    @property
    def name(self) -> Optional[str]:
        """Return the batch name."""
        return self._name

    @property
    def jobs(self) -> list[QuantumJob]:
        """Return the list of jobs submitted within this batch."""
        return list(self._jobs)

    def _register_job(self, job: QuantumJob) -> None:
        """Register a job as part of this batch.

        Called internally by QuantumDevice.run() when an active batch
        context is detected.
        """
        self._jobs.append(job)

    def __enter__(self) -> BatchJobSession:
        """Open the batch session.

        Creates a batch on the backend and sets the context variable
        so that subsequent QuantumDevice.run() calls include the
        batchJobQrn in their job submissions.
        """
        if _active_batch.get(None) is not None:
            raise RuntimeError(
                "Cannot nest BatchJobSession contexts. A batch session is already active."
            )

        self._batch_data = self.client.create_batch(
            name=self._name,
            tags=self._tags,
            metadata=self._metadata,
        )
        self._token = _active_batch.set(self._batch_data.batchJobQrn)
        self._session_token = _active_batch_session.set(self)
        logger.info("Opened batch session: %s", self._batch_data.batchJobQrn)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the batch session.

        Resets the context variable and closes the batch on the backend.
        If an on_all_complete callback was registered, blocks until all
        jobs reach terminal state and then invokes the callback.
        """
        # Reset context variables first (no more jobs can be tagged)
        if self._token is not None:
            _active_batch.reset(self._token)
            self._token = None
        if self._session_token is not None:
            _active_batch_session.reset(self._session_token)
            self._session_token = None

        # Close the batch on the backend
        if self._batch_data is not None:
            try:
                self._batch_data = self.client.close_batch(self._batch_data.batchJobQrn)
                logger.info("Closed batch session: %s", self._batch_data.batchJobQrn)
            except Exception as err:
                logger.error("Failed to close batch: %s", err)

        # If callback registered, wait for results and invoke
        if self._on_complete_callback is not None:
            try:
                batch_result = self.results(
                    timeout=self._on_complete_timeout,
                    poll_interval=self._on_complete_poll_interval,
                )
                self._on_complete_callback(batch_result.results)
            except Exception as err:
                logger.error("on_all_complete callback failed: %s", err)

        return False  # Don't suppress exceptions

    def status(self) -> BatchStatus:
        """Fetch and return the current batch status from the backend.

        Returns:
            BatchStatus enum value.
        """
        if self._batch_data is None:
            raise RuntimeError("Batch session has not been opened.")
        self._batch_data = self.client.get_batch(self._batch_data.batchJobQrn)
        return self._batch_data.status

    def results(
        self,
        timeout: Optional[int] = None,
        poll_interval: float = 5.0,
    ) -> BatchResult:
        """Wait for all jobs to complete and return a BatchResult.

        Blocks until all jobs reach a terminal state (COMPLETED, FAILED,
        CANCELLED) or until the timeout is reached.

        Args:
            timeout: Maximum seconds to wait. None = wait indefinitely.
            poll_interval: Seconds between status checks per job.

        Returns:
            BatchResult mapping jobQrn -> Result[ResultDataType].

        Raises:
            TimeoutError: If timeout reached before all jobs complete.
            RuntimeError: If batch session was never opened.
        """
        if self._batch_data is None:
            raise RuntimeError("Batch session has not been opened.")

        results: dict[str, Result] = {}
        for job in self._jobs:
            job.wait_for_final_state(timeout=timeout, poll_interval=poll_interval)
            results[str(job.id)] = job.result()

        return BatchResult(batch_id=self._batch_data.batchJobQrn, results=results)

    def cancel(self) -> None:
        """Cancel the batch and all non-terminal jobs.

        Raises:
            RuntimeError: If batch session was never opened.
        """
        if self._batch_data is None:
            raise RuntimeError("Batch session has not been opened.")

        self._batch_data = self.client.cancel_batch(self._batch_data.batchJobQrn)
        logger.info("Cancelled batch: %s", self._batch_data.batchJobQrn)

    def on_all_complete(
        self,
        callback: Callable[[dict[str, Result]], None],
        timeout: Optional[int] = None,
        poll_interval: float = 5.0,
    ) -> None:
        """Register a callback to run when all jobs complete.

        The callback receives a dict mapping jobQrn -> Result[ResultDataType].
        Each Result wraps a ResultDataType (GateModelResultData, AnalogResultData, etc.)
        accessible via result.data, which provides methods like:
          - result.data.get_counts() -> dict[str, int]
          - result.data.get_probabilities() -> dict[str, float]
          - result.data.measurements -> numpy.ndarray

        The callback is invoked during __exit__ (when the context manager closes).
        It blocks until all jobs reach terminal state.

        Args:
            callback: Function accepting dict[str, Result].
                Example:
                    def analyze(results):
                        for job_id, result in results.items():
                            counts = result.data.get_counts()
                            print(f"{job_id}: {counts}")
            timeout: Max seconds to wait for all jobs. None = indefinite.
            poll_interval: Seconds between status polls per job.

        Example:
            >>> with BatchJobSession(name="sweep") as batch:
            ...     for circuit in circuits:
            ...         device.run(circuit)
            ...     batch.on_all_complete(analyze, timeout=600)

        Cross-references:
            - Result class: qbraid/runtime/result.py
            - ResultDataType: qbraid/runtime/result_data.py
            - GateModelResultData.get_counts(): result_data.py
        """
        self._on_complete_callback = callback
        self._on_complete_timeout = timeout
        self._on_complete_poll_interval = poll_interval
