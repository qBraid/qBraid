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
Module defining GroupJobSession context manager and GroupResult container.

"""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING, Any, Callable

from qbraid_core.services.runtime import QuantumRuntimeClient

from qbraid._logging import logger
from qbraid.runtime.result import Result

if TYPE_CHECKING:
    from qbraid_core.services.runtime.schemas.group import GroupJob, GroupStatus

    from qbraid.runtime.job import QuantumJob


# Thread-safe context variables for tracking active group.
# NOTE: ContextVar is subscripted at runtime (not lazy like annotations),
# so we must use a string forward ref for GroupJobSession.

# Var for the groupJobQrn string, which is included in job submissions by QbraidDevice.run()
_active_group: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_active_group", default=None
)

# Var for the active GroupJobSession instance, which is read by QbraidDevice.submit()
# to register jobs with the session.
_active_group_session: contextvars.ContextVar["GroupJobSession | None"] = contextvars.ContextVar(
    "_active_group_session", default=None
)


def get_active_group() -> str | None:
    """Return the groupJobQrn of the currently active group, or None.

    Called by QbraidDevice.run() to check if jobs should be tagged
    with a group identifier.
    """
    return _active_group.get(None)


def get_active_group_session() -> GroupJobSession | None:
    """Return the active GroupJobSession, or None.

    Called by QbraidDevice.submit() to register jobs
    with the active group session.
    """
    return _active_group_session.get(None)


def reset_active_group(token: contextvars.Token) -> None:
    """Reset the active group QRN to its previous value."""
    _active_group.reset(token)


def reset_active_group_session(token: contextvars.Token) -> None:
    """Reset the active group session to its previous value."""
    _active_group_session.reset(token)


class GroupResult:
    """Container for results of all jobs in a group.

    Exposes the raw ``results`` mapping for direct access, plus
    convenience helpers for filtering by success. Supports indexing,
    iteration, and ``len()`` via the underlying mapping.

    Attributes:
        group_id: The groupJobQrn identifier.
        results: Mapping of jobQrn -> Result[ResultDataType].

    Example:
        >>> group_result = group.results()
        >>> for job_id, result in group_result.results.items():
        ...     counts = result.data.get_counts()
        ...     print(f"{job_id}: {counts}")
    """

    def __init__(self, group_id: str, results: dict[str, Result]):
        self.group_id = group_id
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
            f"GroupResult(group_id='{self.group_id}', "
            f"total={len(self)}, successful={success}, failed={fail})"
        )


class GroupJobSession:
    """Context manager for grouping quantum job submissions into a group.

    Jobs submitted via QbraidDevice.run() within this context are
    automatically tagged with the group's QRN. The group supports
    cross-device and cross-provider job submissions for qBraid
    native devices.

    Can be used as a context manager or opened/closed manually for
    interactive workflows (notebooks, REPL).

    Args:
        name: Optional human-readable name for the group.
        tags: Optional tags for filtering/organizing groups.
        metadata: Optional metadata dict.
        client: Optional QuantumRuntimeClient instance. If not provided,
            a default client is created.
        max_ttl: Optional max time-to-live in seconds (1–86400). After this
            duration, the group is automatically closed by the backend.
            Defaults to None (backend default of 3600s / 1 hour).

    Example (context manager):
        >>> from qbraid.runtime import GroupJobSession
        >>> with GroupJobSession(name="sweep") as group:
        ...     job1 = device_a.run(circuit_1)
        ...     job2 = device_b.run(circuit_2)
        >>> results = group.results(timeout=300)
        >>> for job_id, result in results.items():
        ...     print(result.data.get_counts())

    Example (manual open/close):
        >>> group = GroupJobSession(name="interactive")
        >>> group.open()
        >>> job1 = device_a.run(circuit_1)
        >>> job2 = device_b.run(circuit_2)
        >>> group.close()
        >>> results = group.results(timeout=300)

    Cross-references:
        - Context variable read by: QbraidDevice.submit() (native/device.py:92-147)
        - Core schemas: qbraid_core.services.runtime.schemas (GroupJob, GroupStatus)
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
        self._group_data: GroupJob | None = None
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
            self._client = QuantumRuntimeClient()
        return self._client

    @property
    def group_id(self) -> str | None:
        """Return the group QRN, or None if not yet opened."""
        return self._group_data.groupJobQrn if self._group_data else None

    @property
    def name(self) -> str | None:
        """Return the group name."""
        return self._name

    @property
    def max_ttl(self) -> int | None:
        """Return the max TTL in seconds, or None."""
        return self._max_ttl

    @property
    def jobs(self) -> list[QuantumJob]:
        """Return the list of jobs submitted within this group."""
        return list(self._jobs)

    def _register_job(self, job: QuantumJob) -> None:
        """Register a job as part of this group.

        Called internally by QbraidDevice.run() when an active group
        context is detected.
        """
        self._jobs.append(job)

    def _reset_context(self) -> None:
        """Reset context variables so no further jobs are tagged with this group."""
        if self._token is not None:
            reset_active_group(self._token)
            self._token = None
        if self._session_token is not None:
            reset_active_group_session(self._session_token)
            self._session_token = None

    def open(self) -> GroupJobSession:
        """Open the group session.

        Creates a group on the backend and sets the context variable
        so that subsequent QbraidDevice.run() calls include the
        groupJobQrn in their job submissions.

        Returns:
            self, for chaining.

        Raises:
            RuntimeError: If a group session is already active.
        """
        if get_active_group() is not None:
            raise RuntimeError(
                "Cannot nest GroupJobSession contexts. A group session is already active."
            )

        # Reset mutable state so the session can be safely reused
        self._jobs = []
        self._on_complete_callback = None
        self._on_complete_timeout = None
        self._on_complete_poll_interval = 5

        self._group_data = self.client.create_group(
            name=self._name,
            tags=self._tags,
            metadata=self._metadata,
            max_ttl=self._max_ttl,
        )
        self._token = _active_group.set(self._group_data.groupJobQrn)
        self._session_token = _active_group_session.set(self)
        logger.info("Opened group session: %s", self._group_data.groupJobQrn)
        return self

    def close(self) -> None:
        """Close the group session.

        Resets context variables and closes the group on the backend.
        Unlike ``__exit__``, errors propagate to the caller and the
        ``on_all_complete`` callback is **not** triggered.

        Raises:
            RuntimeError: If the session has not been opened.
        """
        if self._group_data is None:
            raise RuntimeError("Group session has not been opened.")

        self._reset_context()

        # Close the group on the backend (skip if already in a terminal state,
        # e.g. auto-closed by TTL expiry, or cancelled)
        current_status = getattr(self._group_data.status, "value", self._group_data.status)
        terminal_statuses = {"CLOSED", "COMPLETED", "FAILED", "CANCELLED"}
        if current_status not in terminal_statuses:
            self._group_data = self.client.close_group(self._group_data.groupJobQrn)
            logger.info("Closed group session: %s", self._group_data.groupJobQrn)
        else:
            # Refresh to get latest state from backend
            self._group_data = self.client.get_group(self._group_data.groupJobQrn)
            logger.info(
                "Group already %s, skipping close: %s",
                current_status,
                self._group_data.groupJobQrn,
            )

    def __enter__(self) -> GroupJobSession:
        """Open the group session (delegates to :meth:`open`)."""
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the group session.

        Delegates to :meth:`close` for context-var reset and backend
        close, then runs the ``on_all_complete`` callback if registered.
        Errors from ``close()`` and the callback are logged, not raised.
        Returns ``None`` implicitly so any exception raised inside the
        ``with`` block is not suppressed.
        """
        try:
            self.close()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("Failed to close group: %s", err)

        # If callback registered, wait for results and invoke
        if self._on_complete_callback is not None:
            try:
                group_result = self.results(
                    timeout=self._on_complete_timeout,
                    poll_interval=self._on_complete_poll_interval,
                )
                self._on_complete_callback(group_result.results)
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.error("on_all_complete callback failed: %s", err)

    def status(self) -> GroupStatus:
        """Fetch and return the current group status from the backend.

        Returns:
            GroupStatus enum value.
        """
        if self._group_data is None:
            raise RuntimeError("Group session has not been opened.")
        self._group_data = self.client.get_group(self._group_data.groupJobQrn)
        return self._group_data.status

    def results(
        self,
        timeout: int | None = None,
        poll_interval: int = 5,
    ) -> GroupResult:
        """Wait for all jobs to complete and return a GroupResult.

        Blocks until all jobs reach a terminal state (COMPLETED, FAILED,
        CANCELLED) or until the timeout is reached.

        Args:
            timeout: Maximum seconds to wait **per job**. ``None`` = wait
                indefinitely. Note: this is applied per job, not across the
                whole group, so with N jobs the total blocking time may
                reach up to N * timeout seconds.
            poll_interval: Seconds between status checks per job.

        Returns:
            GroupResult mapping jobQrn -> Result[ResultDataType].

        Raises:
            TimeoutError: If timeout reached before a job completes.
            RuntimeError: If group session was never opened.
        """
        if self._group_data is None:
            raise RuntimeError("Group session has not been opened.")

        results: dict[str, Result] = {}
        for job in self._jobs:
            job.wait_for_final_state(timeout=timeout, poll_interval=poll_interval)
            results[str(job.id)] = job.result()

        return GroupResult(group_id=self._group_data.groupJobQrn, results=results)

    def cancel(self) -> None:
        """Cancel the group and all non-terminal jobs.

        Also resets context variables so that no further jobs are tagged
        with this group and a new ``GroupJobSession`` can be opened.

        Raises:
            RuntimeError: If group session was never opened.
        """
        if self._group_data is None:
            raise RuntimeError("Group session has not been opened.")

        self._reset_context()

        self._group_data = self.client.cancel_group(self._group_data.groupJobQrn)
        logger.info("Cancelled group: %s", self._group_data.groupJobQrn)

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
                time may reach up to N * timeout seconds for N jobs.
            poll_interval: Seconds between status polls per job.

        Example:
            >>> with GroupJobSession(name="sweep") as group:
            ...     for circuit in circuits:
            ...         device.run(circuit)
            ...     group.on_all_complete(analyze, timeout=600)

        Cross-references:
            - Result class: qbraid/runtime/result.py
            - ResultDataType: qbraid/runtime/result_data.py
            - GateModelResultData.get_counts(): result_data.py
        """
        self._on_complete_callback = callback
        self._on_complete_timeout = timeout
        self._on_complete_poll_interval = poll_interval
