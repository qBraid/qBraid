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
from typing import TYPE_CHECKING, Any, Callable

from qbraid._logging import logger
from qbraid.runtime.result import Result

if TYPE_CHECKING:
    from qbraid_core.services.runtime.schemas import BatchJob, BatchStatus

    from qbraid.runtime.job import QuantumJob


# Thread-safe context variables for tracking active batch.
# NOTE: ContextVar is subscripted at runtime (not lazy like annotations),
# so we must use a string forward ref for BatchJobSession.
_active_batch: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_active_batch", default=None
)
_active_batch_session: contextvars.ContextVar["BatchJobSession | None"] = contextvars.ContextVar(
    "_active_batch_session", default=None
)


def get_active_batch() -> str | None:
    """Return the batchJobQrn of the currently active batch, or None.

    Called by QbraidDevice.run() to check if jobs should be tagged
    with a batch identifier.
    """
    return _active_batch.get(None)


def get_active_batch_session() -> BatchJobSession | None:
    """Return the active BatchJobSession, or None.

    Called by QbraidDevice.submit() to register jobs
    with the active batch session.
    """
    return _active_batch_session.get(None)


class BatchResult:
    """Container for results of all jobs in a batch.

    Exposes the raw ``results`` mapping for direct access, plus
    convenience helpers for filtering by success. Supports indexing,
    iteration, and ``len()`` via the underlying mapping.

    Attributes:
        batch_id: The batchJobQrn identifier.
        results: Mapping of jobQrn -> Result[ResultDataType].

    Example:
        >>> batch_result = batch.results()
        >>> for job_id, result in batch_result.results.items():
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

    Jobs submitted via QbraidDevice.run() within this context are
    automatically tagged with the batch's QRN. The batch supports
    cross-device and cross-provider job submissions for qBraid
    native devices.

    Can be used as a context manager or opened/closed manually for
    interactive workflows (notebooks, REPL).

    Args:
        name: Optional human-readable name for the batch.
        tags: Optional tags for filtering/organizing batches.
        metadata: Optional metadata dict.
        client: Optional QuantumRuntimeClient instance. If not provided,
            a default client is created.
        max_ttl: Optional max time-to-live in seconds (1–86400). After this
            duration, the batch is automatically closed by the backend.
            Defaults to None (backend default of 3600s / 1 hour).

    Example (context manager):
        >>> from qbraid.runtime import BatchJobSession
        >>> with BatchJobSession(name="sweep") as batch:
        ...     job1 = device_a.run(circuit_1)
        ...     job2 = device_b.run(circuit_2)
        >>> results = batch.results(timeout=300)
        >>> for job_id, result in results.items():
        ...     print(result.data.get_counts())

    Example (manual open/close):
        >>> batch = BatchJobSession(name="interactive")
        >>> batch.open()
        >>> job1 = device_a.run(circuit_1)
        >>> job2 = device_b.run(circuit_2)
        >>> batch.close()
        >>> results = batch.results(timeout=300)

    Cross-references:
        - Context variable read by: QbraidDevice.submit() (native/device.py:92-147)
        - Core schemas: qbraid_core.services.runtime.schemas (BatchJob, BatchStatus)
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        name: str | None = None,
        tags: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        client: Any | None = None,
        max_ttl: int | None = None,
    ):
        if max_ttl is not None and (max_ttl < 1 or max_ttl > 86400):
            raise ValueError(f"max_ttl must be between 1 and 86400 seconds, got {max_ttl}")
        self._name = name
        self._tags = tags or {}
        self._metadata = metadata or {}
        self._client = client
        self._max_ttl = max_ttl
        self._batch_data: BatchJob | None = None
        self._jobs: list[QuantumJob] = []
        self._token: contextvars.Token | None = None
        self._session_token: contextvars.Token | None = None
        self._on_complete_callback: Callable[[dict[str, Result]], None] | None = None
        self._on_complete_timeout: int | None = None
        self._on_complete_poll_interval: int = 5

    @property
    def client(self):
        """Lazily initialize the QuantumRuntimeClient."""
        if self._client is None:
            from qbraid_core.services.runtime import (  # pylint: disable=import-outside-toplevel
                QuantumRuntimeClient,
            )

            self._client = QuantumRuntimeClient()
        return self._client

    @property
    def batch_id(self) -> str | None:
        """Return the batch QRN, or None if not yet opened."""
        return self._batch_data.batchJobQrn if self._batch_data else None

    @property
    def name(self) -> str | None:
        """Return the batch name."""
        return self._name

    @property
    def max_ttl(self) -> int | None:
        """Return the max TTL in seconds, or None."""
        return self._max_ttl

    @property
    def jobs(self) -> list[QuantumJob]:
        """Return the list of jobs submitted within this batch."""
        return list(self._jobs)

    def _register_job(self, job: QuantumJob) -> None:
        """Register a job as part of this batch.

        Called internally by QbraidDevice.run() when an active batch
        context is detected.
        """
        self._jobs.append(job)

    def open(self) -> BatchJobSession:
        """Open the batch session.

        Creates a batch on the backend and sets the context variable
        so that subsequent QbraidDevice.run() calls include the
        batchJobQrn in their job submissions.

        Returns:
            self, for chaining.

        Raises:
            RuntimeError: If a batch session is already active.
        """
        if _active_batch.get(None) is not None:
            raise RuntimeError(
                "Cannot nest BatchJobSession contexts. A batch session is already active."
            )

        # Reset mutable state so the session can be safely reused
        self._jobs = []
        self._on_complete_callback = None
        self._on_complete_timeout = None
        self._on_complete_poll_interval = 5

        self._batch_data = self.client.create_batch(
            name=self._name,
            tags=self._tags,
            metadata=self._metadata,
            max_ttl=self._max_ttl,
        )
        self._token = _active_batch.set(self._batch_data.batchJobQrn)
        self._session_token = _active_batch_session.set(self)
        logger.info("Opened batch session: %s", self._batch_data.batchJobQrn)
        return self

    def close(self) -> None:
        """Close the batch session.

        Resets context variables and closes the batch on the backend.
        Unlike ``__exit__``, errors propagate to the caller and the
        ``on_all_complete`` callback is **not** triggered.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        if self._batch_data is None:
            raise RuntimeError("Batch session has not been opened.")

        # Reset context variables first (no more jobs can be tagged)
        if self._token is not None:
            _active_batch.reset(self._token)
            self._token = None
        if self._session_token is not None:
            _active_batch_session.reset(self._session_token)
            self._session_token = None

        # Close the batch on the backend (skip if already in a terminal state,
        # e.g. auto-closed by TTL expiry, or cancelled)
        current_status = getattr(self._batch_data.status, "value", self._batch_data.status)
        terminal_statuses = {"CLOSED", "COMPLETED", "FAILED", "CANCELLED"}
        if current_status not in terminal_statuses:
            self._batch_data = self.client.close_batch(self._batch_data.batchJobQrn)
            logger.info("Closed batch session: %s", self._batch_data.batchJobQrn)
        else:
            # Refresh to get latest state from backend
            self._batch_data = self.client.get_batch(self._batch_data.batchJobQrn)
            logger.info(
                "Batch already %s, skipping close: %s",
                current_status,
                self._batch_data.batchJobQrn,
            )

    def __enter__(self) -> BatchJobSession:
        """Open the batch session (delegates to :meth:`open`)."""
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the batch session.

        Delegates to :meth:`close` for context-var reset and backend
        close, then runs the ``on_all_complete`` callback if registered.
        Errors from ``close()`` and the callback are logged, not raised.
        Returns ``None`` implicitly so any exception raised inside the
        ``with`` block is not suppressed.
        """
        try:
            self.close()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("Failed to close batch: %s", err)

        # If callback registered, wait for results and invoke
        if self._on_complete_callback is not None:
            try:
                batch_result = self.results(
                    timeout=self._on_complete_timeout,
                    poll_interval=self._on_complete_poll_interval,
                )
                self._on_complete_callback(batch_result.results)
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.error("on_all_complete callback failed: %s", err)

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
        timeout: int | None = None,
        poll_interval: int = 5,
    ) -> BatchResult:
        """Wait for all jobs to complete and return a BatchResult.

        Blocks until all jobs reach a terminal state (COMPLETED, FAILED,
        CANCELLED) or until the timeout is reached.

        Args:
            timeout: Maximum seconds to wait **per job**. ``None`` = wait
                indefinitely. Note: this is applied per job, not across the
                whole batch, so with N jobs the total blocking time may
                reach up to N × timeout seconds.
            poll_interval: Seconds between status checks per job.

        Returns:
            BatchResult mapping jobQrn -> Result[ResultDataType].

        Raises:
            TimeoutError: If timeout reached before a job completes.
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
        timeout: int | None = None,
        poll_interval: int = 5,
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
            timeout: Max seconds to wait **per job** for terminal state.
                ``None`` = indefinite. Applied per job, so total blocking
                time may reach up to N × timeout seconds for N jobs.
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
