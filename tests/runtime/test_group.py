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

"""Unit tests for GroupJobSession and GroupResult."""

import threading
from unittest.mock import MagicMock, patch

import pytest
from qbraid_core.services.runtime.schemas import Program

from qbraid.runtime.group import (
    GroupJobSession,
    GroupResult,
    _active_group,
    _active_group_session,
    get_active_group,
    get_active_group_session,
    reset_active_group,
    reset_active_group_session,
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
# A. GroupJobSession lifecycle
# ===========================================================================


class TestGroupJobSessionLifecycle:
    """Context entry/exit and property tests."""

    def test_enter_creates_group_and_sets_context(self):
        """Verify __enter__ creates a group and populates context vars."""
        client = MockClient()
        session = GroupJobSession(name="test-group", client=client)

        with session as group:
            assert group is session
            assert group.group_id is not None
            assert group.group_id.startswith("qbraid:group:")
            assert get_active_group() == group.group_id
            assert get_active_group_session() is session

    def test_exit_resets_context_and_closes_group(self):
        """Verify __exit__ resets context vars and closes the group."""
        client = MockClient()
        session = GroupJobSession(name="close-test", client=client)

        with session:
            assert get_active_group() is not None

        # After exit, context variables are reset
        assert get_active_group() is None
        assert get_active_group_session() is None

    def test_group_id_none_before_enter(self):
        """Verify group_id is None before the session is opened."""
        session = GroupJobSession(client=MockClient())
        assert session.group_id is None

    def test_name_property(self):
        """Verify the name property returns the user-supplied name."""
        session = GroupJobSession(name="my-group", client=MockClient())
        assert session.name == "my-group"

    def test_name_none_by_default(self):
        """Verify name defaults to None when not provided."""
        session = GroupJobSession(client=MockClient())
        assert session.name is None

    def test_jobs_property_empty_initially(self):
        """Verify the jobs list is empty before any registration."""
        session = GroupJobSession(client=MockClient())
        assert not session.jobs

    def test_jobs_returns_copy(self):
        """Verify jobs property returns a copy, not the internal list."""
        client = MockClient()
        session = GroupJobSession(client=client)
        with session:
            mock_job = _make_mock_job("job-1")
            session._register_job(mock_job)
            jobs = session.jobs
            jobs.append("extra")  # mutating the copy
            assert len(session.jobs) == 1  # original unchanged

    def test_nested_group_raises_runtime_error(self):
        """Verify that nesting GroupJobSession contexts raises RuntimeError."""
        client = MockClient()
        with GroupJobSession(name="outer", client=client):
            with pytest.raises(RuntimeError, match="Cannot nest"):
                with GroupJobSession(name="inner", client=client):
                    pass  # pragma: no cover


# ===========================================================================
# A2. Manual open()/close()
# ===========================================================================


class TestManualOpenClose:
    """Tests for the explicit open()/close() API."""

    def test_open_creates_group_and_sets_context(self):
        """Verify open() creates a group and sets context vars."""
        client = MockClient()
        session = GroupJobSession(name="manual", client=client)
        result = session.open()

        try:
            assert result is session
            assert session.group_id is not None
            assert session.group_id.startswith("qbraid:group:")
            assert get_active_group() == session.group_id
            assert get_active_group_session() is session
        finally:
            session.close()

    def test_close_resets_context_and_closes_group(self):
        """Verify close() resets context vars and transitions to CLOSED."""
        client = MockClient()
        session = GroupJobSession(name="close-manual", client=client)
        session.open()
        session.close()

        assert get_active_group() is None
        assert get_active_group_session() is None
        assert session._group_data.status.value == "CLOSED"

    def test_close_before_open_raises(self):
        """Verify close() before open() raises RuntimeError."""
        session = GroupJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.close()

    def test_close_skips_close_after_cancel(self):
        """Verify close() is a no-op after cancel(), keeping CANCELLED status."""
        client = MockClient()
        session = GroupJobSession(client=client)
        session.open()
        session.cancel()
        session.close()

        assert session._group_data.status.value == "CANCELLED"

    def test_manual_reuse(self):
        """Verify a session can be opened, closed, and reopened with fresh state."""
        client = MockClient()
        session = GroupJobSession(client=client)

        # First open/close cycle
        session.open()
        first_id = session.group_id
        session._register_job(_make_mock_job("job-a"))
        assert len(session.jobs) == 1
        session.close()
        assert get_active_group() is None

        # Second open/close cycle — fresh state
        session.open()
        second_id = session.group_id
        assert second_id != first_id
        assert len(session.jobs) == 0
        session.close()

    def test_open_returns_self(self):
        """Verify open() returns the session instance for chaining."""
        client = MockClient()
        session = GroupJobSession(client=client)
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
        """Verify _register_job() appends a job to the internal list."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            job = _make_mock_job("job-a")
            group._register_job(job)
            assert len(group.jobs) == 1
            assert group.jobs[0].id == "job-a"

    def test_multiple_jobs_registered(self):
        """Verify multiple jobs can be registered in a single session."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            for i in range(5):
                group._register_job(_make_mock_job(f"job-{i}"))
            assert len(group.jobs) == 5


# ===========================================================================
# C. Error handling
# ===========================================================================


class TestErrorHandling:
    """Pre-entry errors and __exit__ error resilience."""

    def test_status_before_enter_raises(self):
        """Verify status() before open raises RuntimeError."""
        session = GroupJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.status()

    def test_results_before_enter_raises(self):
        """Verify results() before open raises RuntimeError."""
        session = GroupJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.results()

    def test_cancel_before_enter_raises(self):
        """Verify cancel() before open raises RuntimeError."""
        session = GroupJobSession(client=MockClient())
        with pytest.raises(RuntimeError, match="has not been opened"):
            session.cancel()

    def test_close_group_failure_logged_not_raised(self):
        """If close_group() throws in __exit__, exception is logged but not raised."""
        client = MockClient()
        client.close_group = MagicMock(side_effect=Exception("API down"))

        with patch("qbraid.runtime.group.logger") as mock_logger:
            with GroupJobSession(client=client):
                pass  # __exit__ calls close_group which fails

        mock_logger.error.assert_called_once()
        assert "Failed to close group" in mock_logger.error.call_args[0][0]

    def test_callback_failure_logged_not_raised(self):
        """If the on_all_complete callback throws, it's logged, not raised."""
        client = MockClient()

        def bad_callback(results):
            raise ValueError("callback boom")

        with patch("qbraid.runtime.group.logger") as mock_logger:
            with GroupJobSession(client=client) as group:
                group.on_all_complete(bad_callback, timeout=1)
                # No jobs, so results() returns empty GroupResult

        # Check that the error was logged
        error_calls = [c for c in mock_logger.error.call_args_list if "callback failed" in str(c)]
        assert len(error_calls) == 1

    def test_exit_does_not_suppress_exceptions(self):
        """An exception raised inside the with-block should propagate."""
        client = MockClient()
        with pytest.raises(ValueError, match="user error"):
            with GroupJobSession(client=client):
                raise ValueError("user error")


# ===========================================================================
# D. cancel() method
# ===========================================================================


class TestCancel:
    """Tests for GroupJobSession.cancel()."""

    def test_cancel_calls_client(self):
        """Verify cancel() updates group data to CANCELLED status."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            group_qrn = group.group_id
            group.cancel()
            # After cancel, the group data should reflect CANCELLED status
            assert group._group_data.status.value == "CANCELLED"
            assert group._group_data.groupJobQrn == group_qrn

    def test_cancel_with_mock_client(self):
        """Verify cancel() calls cancel_group on the client with the correct QRN."""
        client = MagicMock()
        # Simulate create_group return
        mock_group = MagicMock()
        mock_group.groupJobQrn = "qbraid:group:cancel-test"
        client.create_group.return_value = mock_group

        cancel_result = MagicMock()
        cancel_result.groupJobQrn = "qbraid:group:cancel-test"
        client.cancel_group.return_value = cancel_result
        client.close_group.return_value = mock_group

        with GroupJobSession(client=client) as group:
            group.cancel()

        client.cancel_group.assert_called_once_with("qbraid:group:cancel-test")

    def test_cancel_resets_context_vars(self):
        """Verify cancel() resets active group context variables."""
        client = MockClient()
        session = GroupJobSession(client=client)
        session.open()

        assert get_active_group() is not None
        assert get_active_group_session() is session

        session.cancel()

        assert get_active_group() is None
        assert get_active_group_session() is None

    def test_cancel_allows_new_session(self):
        """Verify a new session can be opened after cancelling the previous one."""
        client = MockClient()
        session = GroupJobSession(client=client)
        session.open()
        session.cancel()

        # A new session should be openable after cancel
        session2 = GroupJobSession(client=client)
        session2.open()
        assert get_active_group() == session2.group_id
        session2.close()


# ===========================================================================
# D2. Public reset functions
# ===========================================================================


class TestResetFunctions:
    """Tests for reset_active_group and reset_active_group_session."""

    def test_reset_active_group_restores_previous_value(self):
        """Verify reset_active_group restores the context var to its prior state."""
        token = _active_group.set("qbraid:group:test-123")
        assert get_active_group() == "qbraid:group:test-123"

        reset_active_group(token)
        assert get_active_group() is None

    def test_reset_active_group_session_restores_previous_value(self):
        """Verify reset_active_group_session restores the context var to its prior state."""
        sentinel = MagicMock()
        token = _active_group_session.set(sentinel)
        assert get_active_group_session() is sentinel

        reset_active_group_session(token)
        assert get_active_group_session() is None


# ===========================================================================
# E. results() method
# ===========================================================================


class TestResults:
    """Tests for GroupJobSession.results()."""

    def test_results_waits_for_all_jobs(self):
        """Verify results() waits for each job and collects their results."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            jobs = []
            for i in range(3):
                job = _make_mock_job(f"job-{i}")
                group._register_job(job)
                jobs.append(job)

        result = group.results(timeout=10, poll_interval=1)
        assert isinstance(result, GroupResult)
        assert len(result) == 3

        for job in jobs:
            job.wait_for_final_state.assert_called_once_with(timeout=10, poll_interval=1)
            job.result.assert_called_once()

    def test_results_empty_group(self):
        """Verify results() returns an empty GroupResult for groups with no jobs."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            pass

        result = group.results()
        assert len(result) == 0
        assert result.group_id == group.group_id

    def test_results_maps_job_id_to_result(self):
        """Verify results() maps each job ID to its corresponding Result."""
        client = MockClient()
        r1 = _make_mock_result("job-x", success=True)
        r2 = _make_mock_result("job-y", success=False)

        with GroupJobSession(client=client) as group:
            group._register_job(_make_mock_job("job-x", result=r1))
            group._register_job(_make_mock_job("job-y", result=r2))

        result = group.results()
        assert result["job-x"] is r1
        assert result["job-y"] is r2


# ===========================================================================
# F. on_all_complete() callback
# ===========================================================================


class TestOnAllComplete:
    """Tests for the on_all_complete callback mechanism."""

    def test_callback_invoked_at_exit(self):
        """Verify the callback is invoked with results on context exit."""
        client = MockClient()
        collected = {}

        def callback(results):
            collected.update(results)

        r1 = _make_mock_result("j1", success=True)

        with GroupJobSession(client=client) as group:
            group._register_job(_make_mock_job("j1", result=r1))
            group.on_all_complete(callback, timeout=5, poll_interval=1)

        assert "j1" in collected
        assert collected["j1"] is r1

    def test_callback_respects_timeout_and_poll_interval(self):
        """Verify the callback passes timeout and poll_interval to wait_for_final_state."""
        client = MockClient()
        job = _make_mock_job("j1")

        with GroupJobSession(client=client) as group:
            group._register_job(job)
            group.on_all_complete(lambda r: None, timeout=42, poll_interval=2)

        job.wait_for_final_state.assert_called_once_with(timeout=42, poll_interval=2)

    def test_callback_not_invoked_if_not_registered(self):
        """If no callback is registered, __exit__ just closes without waiting."""
        client = MockClient()
        job = _make_mock_job("j1")

        with GroupJobSession(client=client) as group:
            group._register_job(job)

        # wait_for_final_state should NOT be called if no callback registered
        job.wait_for_final_state.assert_not_called()


# ===========================================================================
# G. GroupResult container
# ===========================================================================


class TestGroupResult:
    """Tests for the GroupResult class."""

    def _make_group_result(self):
        """Create a GroupResult with 3 jobs (2 successful, 1 failed)."""
        r1 = _make_mock_result("j1", success=True)
        r2 = _make_mock_result("j2", success=False)
        r3 = _make_mock_result("j3", success=True)
        results = {"j1": r1, "j2": r2, "j3": r3}
        return GroupResult(group_id="qbraid:group:test", results=results)

    def test_getitem(self):
        """Verify __getitem__ returns the correct result by job ID."""
        gr = self._make_group_result()
        assert gr["j1"].success is True
        assert gr["j2"].success is False

    def test_getitem_missing_raises_keyerror(self):
        """Verify __getitem__ raises KeyError for unknown job IDs."""
        gr = self._make_group_result()
        with pytest.raises(KeyError):
            _ = gr["nonexistent"]

    def test_iter(self):
        """Verify __iter__ yields all job IDs."""
        gr = self._make_group_result()
        keys = list(gr)
        assert set(keys) == {"j1", "j2", "j3"}

    def test_len(self):
        """Verify __len__ returns the number of results."""
        gr = self._make_group_result()
        assert len(gr) == 3

    def test_results_dict_access(self):
        """Verify direct access to the underlying results dict."""
        gr = self._make_group_result()
        items = list(gr.results.items())
        assert len(items) == 3
        assert set(gr.results.keys()) == {"j1", "j2", "j3"}
        for _, val in items:
            assert isinstance(val, Result)

    def test_successful(self):
        """Verify successful() filters to only successful results."""
        gr = self._make_group_result()
        success = gr.successful()
        assert set(success.keys()) == {"j1", "j3"}
        for r in success.values():
            assert r.success is True

    def test_failed(self):
        """Verify failed() filters to only failed results."""
        gr = self._make_group_result()
        failed = gr.failed()
        assert set(failed.keys()) == {"j2"}
        for r in failed.values():
            assert r.success is False

    def test_repr(self):
        """Verify __repr__ includes group_id and summary counts."""
        gr = self._make_group_result()
        s = repr(gr)
        assert "GroupResult" in s
        assert "total=3" in s
        assert "successful=2" in s
        assert "failed=1" in s
        assert "qbraid:group:test" in s

    def test_empty_group_result(self):
        """Verify GroupResult behaves correctly with zero results."""
        gr = GroupResult(group_id="empty", results={})
        assert len(gr) == 0
        assert not list(gr)
        assert gr.successful() == {}
        assert gr.failed() == {}
        assert "total=0" in repr(gr)


# ===========================================================================
# H. Context variable isolation
# ===========================================================================


class TestContextVariableIsolation:
    """Ensure context variables are properly scoped."""

    def test_active_group_none_outside_context(self):
        """Verify get_active_group() returns None outside a session."""
        assert get_active_group() is None

    def test_active_group_session_none_outside_context(self):
        """Verify get_active_group_session() returns None outside a session."""
        assert get_active_group_session() is None

    def test_active_group_set_inside_context(self):
        """Verify get_active_group() returns the group QRN inside a session."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            assert get_active_group() is not None
            assert get_active_group() == group.group_id

    def test_active_group_session_set_inside_context(self):
        """Verify get_active_group_session() returns the session inside a context."""
        client = MockClient()
        session = GroupJobSession(client=client)
        with session:
            assert get_active_group_session() is session

    def test_both_reset_after_exit(self):
        """Verify both context vars are None after exiting the session."""
        client = MockClient()
        with GroupJobSession(client=client):
            pass
        assert get_active_group() is None
        assert get_active_group_session() is None

    def test_context_reset_even_on_exception(self):
        """Verify context vars are reset even when an exception is raised."""
        client = MockClient()
        with pytest.raises(RuntimeError):
            with GroupJobSession(client=client):
                raise RuntimeError("boom")
        assert get_active_group() is None
        assert get_active_group_session() is None


# ===========================================================================
# I. Lazy client initialization
# ===========================================================================


class TestLazyClientInit:
    """Tests for lazy client property."""

    def test_provided_client_used_directly(self):
        """Verify a provided client is returned without lazy initialization."""
        client = MockClient()
        session = GroupJobSession(client=client)
        assert session.client is client

    def test_lazy_init_creates_client(self):
        """When no client is provided, accessing .client creates a QuantumRuntimeClient."""
        group = GroupJobSession()
        assert group._client is None  # noqa: SLF001
        # Verify that accessing .client triggers lazy init via the import path
        mock_client_cls = MagicMock()
        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        with patch(
            "qbraid.runtime.group.QuantumRuntimeClient",
            mock_client_cls,
        ):
            assert group.client is mock_instance

    def test_lazy_init_imports_and_creates(self):
        """Verify the lazy init code path via mock."""
        mock_client_cls = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance

        session = GroupJobSession()
        assert session._client is None

        with patch(
            "qbraid.runtime.group.QuantumRuntimeClient",
            mock_client_cls,
        ):
            result = session.client

        assert result is mock_client_instance
        mock_client_cls.assert_called_once()


# ===========================================================================
# J. status() method
# ===========================================================================


class TestStatus:
    """Tests for GroupJobSession.status()."""

    def test_status_calls_get_group(self):
        """Verify status() fetches the current group status from the client."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            status = group.status()
            # MockClient.get_group returns OPEN status
            assert status.value == "OPEN"

    def test_status_updates_group_data(self):
        """Verify status() refreshes the cached group data."""
        client = MagicMock()
        mock_group = MagicMock()
        mock_group.groupJobQrn = "qbraid:group:status-test"
        client.create_group.return_value = mock_group

        updated_group = MagicMock()
        updated_group.status = "COMPLETED"
        client.get_group.return_value = updated_group
        client.close_group.return_value = mock_group

        with GroupJobSession(client=client) as group:
            group.status()

        # get_group called twice: once from status(), once from close()
        # (close() refreshes when group is already in a terminal state)
        assert client.get_group.call_count == 2


# ===========================================================================
# K. Session reuse — state reset on re-entry
# ===========================================================================


class TestSessionReuse:
    """Verify that re-entering a session resets mutable state."""

    def test_jobs_reset_on_reentry(self):
        """Verify jobs list is cleared when re-entering a session."""
        client = MockClient()
        session = GroupJobSession(client=client)

        with session as group:
            group._register_job(_make_mock_job("job-first-run"))
            assert len(group.jobs) == 1

        # Re-enter the same session
        with session as group:
            assert len(group.jobs) == 0  # jobs must be empty

    def test_callback_reset_on_reentry(self):
        """Verify on_all_complete callback is cleared on re-entry."""
        client = MockClient()
        session = GroupJobSession(client=client)

        with session as group:
            group.on_all_complete(lambda r: None, timeout=42)

        with session as group:
            # Callback should be cleared; no waiting should occur
            assert group._on_complete_callback is None
            assert group._on_complete_timeout is None


# ===========================================================================
# L. Cancel then exit — close_group should be skipped
# ===========================================================================


class TestCancelThenExit:
    """Verify __exit__ does not overwrite CANCELLED status."""

    def test_exit_skips_close_after_cancel(self):
        """Verify __exit__ preserves CANCELLED status instead of closing."""
        client = MockClient()
        with GroupJobSession(client=client) as group:
            group.cancel()
            assert group._group_data.status.value == "CANCELLED"

        # After exit, status should still be CANCELLED (not CLOSED)
        assert group._group_data.status.value == "CANCELLED"

    def test_exit_skips_close_after_cancel_with_mock(self):
        """Verify close_group is not called on the client after cancel."""
        client = MagicMock()
        mock_group = MagicMock()
        mock_group.groupJobQrn = "qbraid:group:cancel-skip"
        client.create_group.return_value = mock_group

        cancel_result = MagicMock()
        cancel_result.groupJobQrn = "qbraid:group:cancel-skip"
        cancel_result.status = MagicMock(value="CANCELLED")
        client.cancel_group.return_value = cancel_result

        with GroupJobSession(client=client) as group:
            group.cancel()

        # close_group should NOT have been called
        client.close_group.assert_not_called()


# ===========================================================================
# M. TTL parameter validation
# ===========================================================================


class TestGroupTTL:
    """Tests for the max_ttl parameter."""

    def test_max_ttl_passed_to_create_group(self):
        """Verify max_ttl is forwarded to the backend on group creation."""
        client = MockClient()
        with GroupJobSession(client=client, max_ttl=7200) as group:
            assert group._group_data.maxTTL == 7200

    def test_max_ttl_none_by_default(self):
        """Verify max_ttl defaults to None when not provided."""
        session = GroupJobSession(client=MockClient())
        assert session.max_ttl is None

    def test_max_ttl_property(self):
        """Verify the max_ttl property returns the configured value."""
        session = GroupJobSession(client=MockClient(), max_ttl=1800)
        assert session.max_ttl == 1800

    def test_max_ttl_exceeds_24h_raises(self):
        """Verify max_ttl > 86400 raises ValueError."""
        with pytest.raises(ValueError, match="max_ttl must be between"):
            GroupJobSession(client=MockClient(), max_ttl=86401)

    def test_max_ttl_zero_raises(self):
        """Verify max_ttl=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_ttl must be between"):
            GroupJobSession(client=MockClient(), max_ttl=0)

    def test_max_ttl_negative_raises(self):
        """Verify negative max_ttl raises ValueError."""
        with pytest.raises(ValueError, match="max_ttl must be between"):
            GroupJobSession(client=MockClient(), max_ttl=-1)


# ===========================================================================
# N. Thread isolation for context variables
# ===========================================================================


class TestThreadIsolation:
    """Verify contextvars are not visible across threads."""

    def test_group_not_visible_in_worker_thread(self):
        """A group opened in the main thread should not be visible in a worker."""
        client = MockClient()
        worker_result = {}

        def worker():
            worker_result["group"] = get_active_group()
            worker_result["session"] = get_active_group_session()

        with GroupJobSession(client=client):
            t = threading.Thread(target=worker)
            t.start()
            t.join()

        assert worker_result["group"] is None
        assert worker_result["session"] is None

    def test_worker_group_not_visible_in_main_thread(self):
        """A group opened in a worker thread should not be visible in main."""
        client = MockClient()
        barrier = threading.Barrier(2, timeout=5)

        def worker():
            with GroupJobSession(client=client):
                barrier.wait()  # signal main that group is open
                barrier.wait()  # wait for main to check

        t = threading.Thread(target=worker)
        t.start()

        barrier.wait()  # wait for worker to open group
        assert get_active_group() is None
        assert get_active_group_session() is None
        barrier.wait()  # let worker exit

        t.join()


# ===========================================================================
# O. Partial-failure registration regression
# ===========================================================================


class TestPartialFailureRegistration:
    """Regression test for per-iteration job registration.

    When ``QbraidDevice.submit()`` fails mid-loop (e.g. the N-th call to
    ``client.create_job`` raises), all jobs created *before* the failure
    must still be registered with the active :class:`GroupJobSession`.

    Prior to the fix, jobs were only registered after the loop completed
    successfully, so a failure mid-loop would leave ``session.jobs``
    empty even though real jobs had been created on the backend —
    causing silent data loss from the SDK's point of view.
    """

    @patch("qbraid.runtime.native.device.QuantumRuntimeClient")
    def test_partial_failure_registers_successful_jobs(self, _mock_client_cls):
        """Successful jobs are registered even if a later create_job raises."""
        # pylint: disable=protected-access,import-outside-toplevel
        from qbraid.runtime.native.device import QbraidDevice

        # Build a fully-mocked QbraidDevice without touching the network.
        mock_profile = MagicMock()
        mock_profile.device_id = "qbraid:qbraid:sim:qir-sv"
        mock_profile.program_spec = None
        mock_profile.noise_models = None

        device = QbraidDevice(profile=mock_profile, client=MagicMock())

        # Configure create_job to return two valid responses then raise.
        # Each response only needs a ``jobQrn`` attribute — that is the only
        # field QbraidDevice.submit() reads from it.
        response_1 = MagicMock(jobQrn="qbraid:qbraid:sim:qir-sv-qjob-000001")
        response_2 = MagicMock(jobQrn="qbraid:qbraid:sim:qir-sv-qjob-000002")

        failing_client = MagicMock()
        failing_client.create_job = MagicMock(
            side_effect=[response_1, response_2, RuntimeError("backend boom")]
        )
        device._client = failing_client

        # Program instances must satisfy the JobRequest pydantic schema.
        programs = [Program(format="qasm2", data="OPENQASM 2.0;") for _ in range(5)]

        with GroupJobSession(client=MockClient()) as group:
            with pytest.raises(RuntimeError, match="backend boom"):
                # Call submit() directly to bypass transpile/validate/prepare,
                # which would otherwise try to load the minimal program.
                device.submit(programs)

            # The two successful jobs must already be registered on the
            # session even though submit() raised before returning.
            assert len(group.jobs) == 2
            assert len(group._jobs) == 2
            # create_job was called exactly three times (2 successes + 1 fail)
            assert failing_client.create_job.call_count == 3
