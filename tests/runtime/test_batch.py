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
Unit tests for BatchJobSession and BatchResult.

"""

# pylint: disable=missing-function-docstring

import threading
from unittest.mock import MagicMock, patch

import pytest
from qbraid_core.services.runtime.schemas import Program

from qbraid.runtime.batch import (
    BatchJobSession,
    BatchResult,
    get_active_batch,
    get_active_batch_session,
)
from qbraid.runtime.result import Result

from ._resources import MockClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_result(job_id: str, success: bool = True) -> Result:
    """Create a minimal Result for testing."""
    data = MagicMock()
    return Result(device_id="mock-device", job_id=job_id, success=success, data=data)


def _make_mock_job(job_id: str, result: Result | None = None):
    """Create a mock QuantumJob-like object."""
    job = MagicMock()
    job.id = job_id
    job.__str__ = lambda self: job_id
    if result is None:
        result = _make_mock_result(job_id)
    job.result.return_value = result
    return job


# ===========================================================================
# A. BatchJobSession lifecycle
# ===========================================================================


class TestBatchJobSessionLifecycle:
    """Context entry/exit and property tests."""

    def test_enter_creates_batch_and_sets_context(self):
        client = MockClient()
        session = BatchJobSession(name="test-batch", client=client)

        with session as batch:
            assert batch is session
            assert batch.batch_id is not None
            assert batch.batch_id.startswith("qbraid:batch:")
            assert get_active_batch() == batch.batch_id
            assert get_active_batch_session() is session

    def test_exit_resets_context_and_closes_batch(self):
        client = MockClient()
        session = BatchJobSession(name="close-test", client=client)

        with session:
            assert get_active_batch() is not None

        # After exit, context variables are reset
        assert get_active_batch() is None
        assert get_active_batch_session() is None

    def test_batch_id_none_before_enter(self):
        session = BatchJobSession(client=MockClient())
        assert session.batch_id is None

    def test_name_property(self):
        session = BatchJobSession(name="my-batch", client=MockClient())
        assert session.name == "my-batch"

    def test_name_none_by_default(self):
        session = BatchJobSession(client=MockClient())
        assert session.name is None

    def test_jobs_property_empty_initially(self):
        session = BatchJobSession(client=MockClient())
        assert not session.jobs

    def test_jobs_returns_copy(self):
        client = MockClient()
        session = BatchJobSession(client=client)
        with session:
            mock_job = _make_mock_job("job-1")
            session._register_job(mock_job)
            jobs = session.jobs
            jobs.append("extra")  # mutating the copy
            assert len(session.jobs) == 1  # original unchanged

    def test_nested_batch_raises_runtime_error(self):
        client = MockClient()
        with BatchJobSession(name="outer", client=client):
            with pytest.raises(RuntimeError, match="Cannot nest"):
                with BatchJobSession(name="inner", client=client):
                    pass  # pragma: no cover


# ===========================================================================
# A2. Manual open()/close()
# ===========================================================================


class TestManualOpenClose:
    """Tests for the explicit open()/close() API."""

    def test_open_creates_batch_and_sets_context(self):
        client = MockClient()
        session = BatchJobSession(name="manual", client=client)
        result = session.open()

        try:
            assert result is session
            assert session.batch_id is not None
            assert session.batch_id.startswith("qbraid:batch:")
            assert get_active_batch() == session.batch_id
            assert get_active_batch_session() is session
        finally:
            session.close()

    def test_close_resets_context_and_closes_batch(self):
        client = MockClient()
        session = BatchJobSession(name="close-manual", client=client)
        session.open()
        session.close()

        assert get_active_batch() is None
        assert get_active_batch_session() is None
        assert session._batch_data.status.value == "CLOSED"

    def test_close_before_open_raises(self):
        session = BatchJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.close()

    def test_close_skips_close_after_cancel(self):
        client = MockClient()
        session = BatchJobSession(client=client)
        session.open()
        session.cancel()
        session.close()

        assert session._batch_data.status.value == "CANCELLED"

    def test_manual_reuse(self):
        client = MockClient()
        session = BatchJobSession(client=client)

        # First open/close cycle
        session.open()
        first_id = session.batch_id
        session._register_job(_make_mock_job("job-a"))
        assert len(session.jobs) == 1
        session.close()
        assert get_active_batch() is None

        # Second open/close cycle — fresh state
        session.open()
        second_id = session.batch_id
        assert second_id != first_id
        assert len(session.jobs) == 0
        session.close()

    def test_open_returns_self(self):
        client = MockClient()
        session = BatchJobSession(client=client)
        try:
            assert session.open() is session
        finally:
            session.close()


# ===========================================================================
# B. Job registration
# ===========================================================================


class TestJobRegistration:
    """Jobs registered via _register_job()."""

    def test_register_job_adds_to_list(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            job = _make_mock_job("job-a")
            batch._register_job(job)
            assert len(batch.jobs) == 1
            assert batch.jobs[0].id == "job-a"

    def test_multiple_jobs_registered(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            for i in range(5):
                batch._register_job(_make_mock_job(f"job-{i}"))
            assert len(batch.jobs) == 5


# ===========================================================================
# C. Error handling
# ===========================================================================


class TestErrorHandling:
    """Pre-entry errors and __exit__ error resilience."""

    def test_status_before_enter_raises(self):
        session = BatchJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.status()

    def test_results_before_enter_raises(self):
        session = BatchJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.results()

    def test_cancel_before_enter_raises(self):
        session = BatchJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.cancel()

    def test_close_batch_failure_logged_not_raised(self):
        """If close_batch() throws in __exit__, exception is logged but not raised."""
        client = MockClient()
        client.close_batch = MagicMock(side_effect=Exception("API down"))

        with patch("qbraid.runtime.batch.logger") as mock_logger:
            with BatchJobSession(client=client):
                pass  # __exit__ calls close_batch which fails

        mock_logger.error.assert_called_once()
        assert "Failed to close batch" in mock_logger.error.call_args[0][0]

    def test_callback_failure_logged_not_raised(self):
        """If the on_all_complete callback throws, it's logged, not raised."""
        client = MockClient()

        def bad_callback(results):
            raise ValueError("callback boom")

        with patch("qbraid.runtime.batch.logger") as mock_logger:
            with BatchJobSession(client=client) as batch:
                batch.on_all_complete(bad_callback, timeout=1)
                # No jobs, so results() returns empty BatchResult

        # Check that the error was logged
        error_calls = [c for c in mock_logger.error.call_args_list if "callback failed" in str(c)]
        assert len(error_calls) == 1

    def test_exit_does_not_suppress_exceptions(self):
        """An exception raised inside the with-block should propagate."""
        client = MockClient()
        with pytest.raises(ValueError, match="user error"):
            with BatchJobSession(client=client):
                raise ValueError("user error")


# ===========================================================================
# D. cancel() method
# ===========================================================================


class TestCancel:
    """Tests for BatchJobSession.cancel()."""

    def test_cancel_calls_client(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            batch_qrn = batch.batch_id
            batch.cancel()
            # After cancel, the batch data should reflect CANCELLED status
            assert batch._batch_data.status.value == "CANCELLED"
            assert batch._batch_data.batchJobQrn == batch_qrn

    def test_cancel_with_mock_client(self):
        client = MagicMock()
        # Simulate create_batch return
        mock_batch = MagicMock()
        mock_batch.batchJobQrn = "qbraid:batch:cancel-test"
        client.create_batch.return_value = mock_batch

        cancel_result = MagicMock()
        cancel_result.batchJobQrn = "qbraid:batch:cancel-test"
        client.cancel_batch.return_value = cancel_result
        client.close_batch.return_value = mock_batch

        with BatchJobSession(client=client) as batch:
            batch.cancel()

        client.cancel_batch.assert_called_once_with("qbraid:batch:cancel-test")


# ===========================================================================
# E. results() method
# ===========================================================================


class TestResults:
    """Tests for BatchJobSession.results()."""

    def test_results_waits_for_all_jobs(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            jobs = []
            for i in range(3):
                job = _make_mock_job(f"job-{i}")
                batch._register_job(job)
                jobs.append(job)

        result = batch.results(timeout=10, poll_interval=1)
        assert isinstance(result, BatchResult)
        assert len(result) == 3

        for job in jobs:
            job.wait_for_final_state.assert_called_once_with(timeout=10, poll_interval=1)
            job.result.assert_called_once()

    def test_results_empty_batch(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            pass

        result = batch.results()
        assert len(result) == 0
        assert result.batch_id == batch.batch_id

    def test_results_maps_job_id_to_result(self):
        client = MockClient()
        r1 = _make_mock_result("job-x", success=True)
        r2 = _make_mock_result("job-y", success=False)

        with BatchJobSession(client=client) as batch:
            batch._register_job(_make_mock_job("job-x", result=r1))
            batch._register_job(_make_mock_job("job-y", result=r2))

        result = batch.results()
        assert result["job-x"] is r1
        assert result["job-y"] is r2


# ===========================================================================
# F. on_all_complete() callback
# ===========================================================================


class TestOnAllComplete:
    """Tests for the on_all_complete callback mechanism."""

    def test_callback_invoked_at_exit(self):
        client = MockClient()
        collected = {}

        def callback(results):
            collected.update(results)

        r1 = _make_mock_result("j1", success=True)

        with BatchJobSession(client=client) as batch:
            batch._register_job(_make_mock_job("j1", result=r1))
            batch.on_all_complete(callback, timeout=5, poll_interval=1)

        assert "j1" in collected
        assert collected["j1"] is r1

    def test_callback_respects_timeout_and_poll_interval(self):
        client = MockClient()
        job = _make_mock_job("j1")

        with BatchJobSession(client=client) as batch:
            batch._register_job(job)
            batch.on_all_complete(lambda r: None, timeout=42, poll_interval=2)

        job.wait_for_final_state.assert_called_once_with(timeout=42, poll_interval=2)

    def test_callback_not_invoked_if_not_registered(self):
        """If no callback is registered, __exit__ just closes without waiting."""
        client = MockClient()
        job = _make_mock_job("j1")

        with BatchJobSession(client=client) as batch:
            batch._register_job(job)

        # wait_for_final_state should NOT be called if no callback registered
        job.wait_for_final_state.assert_not_called()


# ===========================================================================
# G. BatchResult container
# ===========================================================================


class TestBatchResult:
    """Tests for the BatchResult class."""

    def _make_batch_result(self):
        r1 = _make_mock_result("j1", success=True)
        r2 = _make_mock_result("j2", success=False)
        r3 = _make_mock_result("j3", success=True)
        results = {"j1": r1, "j2": r2, "j3": r3}
        return BatchResult(batch_id="qbraid:batch:test", results=results)

    def test_getitem(self):
        br = self._make_batch_result()
        assert br["j1"].success is True
        assert br["j2"].success is False

    def test_getitem_missing_raises_keyerror(self):
        br = self._make_batch_result()
        with pytest.raises(KeyError):
            _ = br["nonexistent"]

    def test_iter(self):
        br = self._make_batch_result()
        keys = list(br)
        assert set(keys) == {"j1", "j2", "j3"}

    def test_len(self):
        br = self._make_batch_result()
        assert len(br) == 3

    def test_results_dict_access(self):
        """Direct access to the underlying ``results`` dict is the canonical
        way to enumerate (jobQrn, Result) pairs."""
        br = self._make_batch_result()
        items = list(br.results.items())
        assert len(items) == 3
        assert set(br.results.keys()) == {"j1", "j2", "j3"}
        for _, val in items:
            assert isinstance(val, Result)

    def test_successful(self):
        br = self._make_batch_result()
        success = br.successful()
        assert set(success.keys()) == {"j1", "j3"}
        for r in success.values():
            assert r.success is True

    def test_failed(self):
        br = self._make_batch_result()
        failed = br.failed()
        assert set(failed.keys()) == {"j2"}
        for r in failed.values():
            assert r.success is False

    def test_repr(self):
        br = self._make_batch_result()
        s = repr(br)
        assert "BatchResult" in s
        assert "total=3" in s
        assert "successful=2" in s
        assert "failed=1" in s
        assert "qbraid:batch:test" in s

    def test_empty_batch_result(self):
        br = BatchResult(batch_id="empty", results={})
        assert len(br) == 0
        assert not list(br)
        assert br.successful() == {}
        assert br.failed() == {}
        assert "total=0" in repr(br)


# ===========================================================================
# H. Context variable isolation
# ===========================================================================


class TestContextVariableIsolation:
    """Ensure context variables are properly scoped."""

    def test_active_batch_none_outside_context(self):
        assert get_active_batch() is None

    def test_active_batch_session_none_outside_context(self):
        assert get_active_batch_session() is None

    def test_active_batch_set_inside_context(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            assert get_active_batch() is not None
            assert get_active_batch() == batch.batch_id

    def test_active_batch_session_set_inside_context(self):
        client = MockClient()
        session = BatchJobSession(client=client)
        with session:
            assert get_active_batch_session() is session

    def test_both_reset_after_exit(self):
        client = MockClient()
        with BatchJobSession(client=client):
            pass
        assert get_active_batch() is None
        assert get_active_batch_session() is None

    def test_context_reset_even_on_exception(self):
        client = MockClient()
        with pytest.raises(RuntimeError):
            with BatchJobSession(client=client):
                raise RuntimeError("boom")
        assert get_active_batch() is None
        assert get_active_batch_session() is None


# ===========================================================================
# I. Lazy client initialization
# ===========================================================================


class TestLazyClientInit:
    """Tests for lazy client property."""

    def test_provided_client_used_directly(self):
        client = MockClient()
        session = BatchJobSession(client=client)
        assert session.client is client

    def test_lazy_init_creates_client(self):
        """When no client is provided, accessing .client creates a QuantumRuntimeClient."""
        batch = BatchJobSession()
        assert batch._client is None  # noqa: SLF001
        # Verify that accessing .client triggers lazy init via the import path
        mock_client_cls = MagicMock()
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        with patch(
            "qbraid_core.services.runtime.QuantumRuntimeClient",
            mock_client_cls,
        ):
            assert batch.client is mock_instance

    def test_lazy_init_imports_and_creates(self):
        """Verify the lazy init code path via mock."""
        mock_client_cls = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        session = BatchJobSession()
        assert session._client is None

        with patch(
            "qbraid_core.services.runtime.QuantumRuntimeClient",
            mock_client_cls,
        ):
            result = session.client

        assert result is mock_client_instance
        mock_client_cls.assert_called_once()


# ===========================================================================
# J. status() method
# ===========================================================================


class TestStatus:
    """Tests for BatchJobSession.status()."""

    def test_status_calls_get_batch(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            status = batch.status()
            # MockClient.get_batch returns OPEN status
            assert status.value == "OPEN"

    def test_status_updates_batch_data(self):
        client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.batchJobQrn = "qbraid:batch:status-test"
        client.create_batch.return_value = mock_batch

        updated_batch = MagicMock()
        updated_batch.status = "COMPLETED"
        client.get_batch.return_value = updated_batch
        client.close_batch.return_value = mock_batch

        with BatchJobSession(client=client) as batch:
            batch.status()

        # get_batch called twice: once from status(), once from close()
        # (close() refreshes when batch is already in a terminal state)
        assert client.get_batch.call_count == 2


# ===========================================================================
# K. Session reuse — state reset on re-entry
# ===========================================================================


class TestSessionReuse:
    """Verify that re-entering a session resets mutable state."""

    def test_jobs_reset_on_reentry(self):
        client = MockClient()
        session = BatchJobSession(client=client)

        with session as batch:
            batch._register_job(_make_mock_job("job-first-run"))
            assert len(batch.jobs) == 1

        # Re-enter the same session
        with session as batch:
            assert len(batch.jobs) == 0  # jobs must be empty

    def test_callback_reset_on_reentry(self):
        client = MockClient()
        session = BatchJobSession(client=client)

        with session as batch:
            batch.on_all_complete(lambda r: None, timeout=42)

        with session as batch:
            # Callback should be cleared; no waiting should occur
            assert batch._on_complete_callback is None
            assert batch._on_complete_timeout is None


# ===========================================================================
# L. Cancel then exit — close_batch should be skipped
# ===========================================================================


class TestCancelThenExit:
    """Verify __exit__ does not overwrite CANCELLED status."""

    def test_exit_skips_close_after_cancel(self):
        client = MockClient()
        with BatchJobSession(client=client) as batch:
            batch.cancel()
            assert batch._batch_data.status.value == "CANCELLED"

        # After exit, status should still be CANCELLED (not CLOSED)
        assert batch._batch_data.status.value == "CANCELLED"

    def test_exit_skips_close_after_cancel_with_mock(self):
        client = MagicMock()
        mock_batch = MagicMock()
        mock_batch.batchJobQrn = "qbraid:batch:cancel-skip"
        client.create_batch.return_value = mock_batch

        cancel_result = MagicMock()
        cancel_result.batchJobQrn = "qbraid:batch:cancel-skip"
        cancel_result.status = MagicMock(value="CANCELLED")
        client.cancel_batch.return_value = cancel_result

        with BatchJobSession(client=client) as batch:
            batch.cancel()

        # close_batch should NOT have been called
        client.close_batch.assert_not_called()


# ===========================================================================
# M. Thread isolation for context variables
# ===========================================================================


class TestBatchTTL:
    """Tests for the max_ttl parameter."""

    def test_max_ttl_passed_to_create_batch(self):
        client = MockClient()
        with BatchJobSession(client=client, max_ttl=7200) as batch:
            assert batch._batch_data.maxTTL == 7200

    def test_max_ttl_none_by_default(self):
        session = BatchJobSession(client=MockClient())
        assert session.max_ttl is None

    def test_max_ttl_property(self):
        session = BatchJobSession(client=MockClient(), max_ttl=1800)
        assert session.max_ttl == 1800

    def test_max_ttl_exceeds_24h_raises(self):
        with pytest.raises(ValueError, match="max_ttl must be between"):
            BatchJobSession(client=MockClient(), max_ttl=86401)

    def test_max_ttl_zero_raises(self):
        with pytest.raises(ValueError, match="max_ttl must be between"):
            BatchJobSession(client=MockClient(), max_ttl=0)

    def test_max_ttl_negative_raises(self):
        with pytest.raises(ValueError, match="max_ttl must be between"):
            BatchJobSession(client=MockClient(), max_ttl=-1)


class TestThreadIsolation:
    """Verify contextvars are not visible across threads."""

    def test_batch_not_visible_in_worker_thread(self):
        """A batch opened in the main thread should not be visible in a worker."""
        client = MockClient()
        worker_result = {}

        def worker():
            worker_result["batch"] = get_active_batch()
            worker_result["session"] = get_active_batch_session()

        with BatchJobSession(client=client):
            t = threading.Thread(target=worker)
            t.start()
            t.join()

        assert worker_result["batch"] is None
        assert worker_result["session"] is None

    def test_worker_batch_not_visible_in_main_thread(self):
        """A batch opened in a worker thread should not be visible in main."""
        client = MockClient()
        barrier = threading.Barrier(2, timeout=5)

        def worker():
            with BatchJobSession(client=client):
                barrier.wait()  # signal main that batch is open
                barrier.wait()  # wait for main to check

        t = threading.Thread(target=worker)
        t.start()

        barrier.wait()  # wait for worker to open batch
        assert get_active_batch() is None
        assert get_active_batch_session() is None
        barrier.wait()  # let worker exit

        t.join()


# ===========================================================================
# N. Partial-failure registration regression
# ===========================================================================


class TestPartialFailureRegistration:
    """Regression test for per-iteration job registration.

    When ``QbraidDevice.submit()`` fails mid-loop (e.g. the N-th call to
    ``client.create_job`` raises), all jobs created *before* the failure
    must still be registered with the active :class:`BatchJobSession`.

    Prior to the fix, jobs were only registered after the loop completed
    successfully, so a failure mid-loop would leave ``session.jobs``
    empty even though real jobs had been created on the backend —
    causing silent data loss from the SDK's point of view.
    """

    def test_partial_failure_registers_successful_jobs(self, mock_qbraid_device):
        """Successful jobs are registered even if a later create_job raises."""
        # pylint: disable=protected-access

        # Swap the device's client for a MagicMock whose create_job returns
        # two valid-looking job responses and then raises on the third call.
        # Each response only needs a ``jobQrn`` attribute — that is the only
        # field QbraidDevice.submit() reads from it.
        response_1 = MagicMock(jobQrn="qbraid:qbraid:sim:qir-sv-qjob-000001")
        response_2 = MagicMock(jobQrn="qbraid:qbraid:sim:qir-sv-qjob-000002")

        failing_client = MagicMock()
        failing_client.create_job = MagicMock(
            side_effect=[response_1, response_2, RuntimeError("backend boom")]
        )
        mock_qbraid_device._client = failing_client

        # Program instances must satisfy the JobRequest pydantic schema.
        programs = [Program(format="qasm2", data="OPENQASM 2.0;") for _ in range(5)]

        with BatchJobSession(client=MockClient()) as batch:
            with pytest.raises(RuntimeError, match="backend boom"):
                # Call submit() directly to bypass transpile/validate/prepare,
                # which would otherwise try to load the minimal program.
                mock_qbraid_device.submit(programs)

            # The two successful jobs must already be registered on the
            # session even though submit() raised before returning.
            assert len(batch.jobs) == 2
            assert len(batch._jobs) == 2
            # create_job was called exactly three times (2 successes + 1 fail)
            assert failing_client.create_job.call_count == 3
