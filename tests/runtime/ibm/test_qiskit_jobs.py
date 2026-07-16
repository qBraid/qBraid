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

# pylint: disable=redefined-outer-name

"""
Unit tests for QiskitRuntimeProvider job listing, retrieval, and IBM API auth.

Tests list_jobs(), get_job(), _exchange_api_key(), _ibm_api_get(), and
_load_ibm_cloud_credentials() using realistic mock data modeled after
actual IBM Quantum REST API responses.
"""

import json
from io import BytesIO
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from qbraid.runtime.exceptions import (
    AuthorizationError,
    JobNotFoundError,
    ResourceNotFoundError,
    RuntimeAPIError,
)
from qbraid.runtime.ibm.provider import QiskitRuntimeProvider, _parse_iam_error

# ---------------------------------------------------------------------------
# Realistic mock data — modeled after IBM Quantum REST API responses
# ---------------------------------------------------------------------------

IBM_JOB_SAMPLER = {
    "id": "d5apdvonsj9s73b7th1g",
    "backend": "ibm_fez",
    "status": "Completed",
    "params": {"optimization_level": 1},
    "program": {"id": "sampler"},
    "created": "2026-04-14T18:30:00Z",
    "ended": "2026-04-14T18:32:15Z",
    "cost": 1.25,
    "usage": {"quantum_seconds": 4.82, "seconds": 135},
    "tags": ["benchmark", "bell-state"],
}

IBM_JOB_ESTIMATOR = {
    "id": "e7bqfxrpwk0t84c9ui2h",
    "backend": "ibm_brisbane",
    "status": "Completed",
    "params": {"optimization_level": 3},
    "program": {"id": "estimator"},
    "created": "2026-04-13T09:15:00Z",
    "ended": "2026-04-13T09:18:42Z",
    "cost": 0.85,
    "usage": {"quantum_seconds": 2.1, "seconds": 222},
    "tags": ["vqe-research"],
}

IBM_JOB_QUEUED = {
    "id": "f9cshztqyl2u95d0vj3i",
    "backend": "ibm_fez",
    "status": "Queued",
    "params": {},
    "program": {"id": "sampler"},
    "created": "2026-04-25T10:00:00Z",
    "cost": 0,
    "tags": [],
}

IBM_JOB_FAILED = {
    "id": "g0dtiu0rzm3v06e1wk4j",
    "backend": "ibm_kyiv",
    "status": "Failed",
    "params": {},
    "program": {"id": "sampler"},
    "created": "2026-04-24T14:00:00Z",
    "ended": "2026-04-24T14:00:05Z",
    "cost": 0,
    "tags": [],
}

IBM_JOBS_RESPONSE = {
    "jobs": [IBM_JOB_SAMPLER, IBM_JOB_ESTIMATOR, IBM_JOB_QUEUED, IBM_JOB_FAILED],
    "count": 4,
}

IBM_METRICS = {
    "timestamps": {
        "created": "2026-04-14T18:30:00Z",
        "running": "2026-04-14T18:30:12Z",
        "finished": "2026-04-14T18:32:15Z",
    },
    "usage": {"quantum_seconds": 4.82, "seconds": 135},
    "num_circuits": 1,
    "num_qubits": 40,
    "qiskit_version": "1.3.2",
}

FAKE_IAM_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.fake_access_token"
FAKE_API_KEY = "xR7k9Lm2nP4qS6tU8vW0yZ3bD5fH1jK"
FAKE_INSTANCE = "crn:v1:bluemix:public:quantum-computing:us-east:a/abc123:def456::"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ibm_api():
    """
    Context manager that mocks both _exchange_api_key and urlopen
    so _ibm_api_get works without real HTTP calls.
    """

    def _make_response(data):
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    return _make_response


@pytest.fixture
def provider():
    """QiskitRuntimeProvider with mocked service initialization."""
    with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService"):
        p = QiskitRuntimeProvider(token=FAKE_API_KEY, channel="ibm_cloud")
        p.token = FAKE_API_KEY
        p.instance = FAKE_INSTANCE
        return p


# ---------------------------------------------------------------------------
# _load_ibm_cloud_credentials
# ---------------------------------------------------------------------------


class TestLoadCredentials:
    """Test loading IBM credentials from ~/.qiskit/qiskit-ibm.json."""

    def test_loads_ibm_cloud_channel(self, tmp_path):
        """Prefers ibm_cloud channel entry."""
        config = {
            "default": {
                "channel": "ibm_quantum_platform",
                "token": "old_token",
                "instance": "old_instance",
            },
            "cloud": {
                "channel": "ibm_cloud",
                "token": FAKE_API_KEY,
                "instance": FAKE_INSTANCE,
            },
        }
        config_file = tmp_path / ".qiskit" / "qiskit-ibm.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config))

        with patch.object(Path, "home", return_value=tmp_path):
            result = QiskitRuntimeProvider._load_ibm_cloud_credentials()

        assert result["token"] == FAKE_API_KEY
        assert result["instance"] == FAKE_INSTANCE

    def test_falls_back_to_first_entry(self, tmp_path):
        """Falls back to first entry when no ibm_cloud channel."""
        config = {
            "only_entry": {
                "channel": "ibm_quantum_platform",
                "token": "fallback_token",
                "instance": "fallback_instance",
            },
        }
        config_file = tmp_path / ".qiskit" / "qiskit-ibm.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(json.dumps(config))

        with patch.object(Path, "home", return_value=tmp_path):
            result = QiskitRuntimeProvider._load_ibm_cloud_credentials()

        assert result["token"] == "fallback_token"

    def test_returns_empty_when_file_missing(self, tmp_path):
        """Returns empty dict when config file doesn't exist."""
        with patch.object(Path, "home", return_value=tmp_path):
            result = QiskitRuntimeProvider._load_ibm_cloud_credentials()

        assert result == {}

    def test_returns_empty_on_invalid_json(self, tmp_path):
        """Returns empty dict on malformed JSON."""
        config_file = tmp_path / ".qiskit" / "qiskit-ibm.json"
        config_file.parent.mkdir(parents=True)
        config_file.write_text("not valid json {{{")

        with patch.object(Path, "home", return_value=tmp_path):
            result = QiskitRuntimeProvider._load_ibm_cloud_credentials()

        assert result == {}


# ---------------------------------------------------------------------------
# _exchange_api_key
# ---------------------------------------------------------------------------


class TestExchangeApiKey:
    """Test IAM token exchange flow."""

    def test_exchanges_key_successfully(self, provider, mock_ibm_api):
        """Exchanges API key for IAM access token."""
        mock_resp = mock_ibm_api({"access_token": FAKE_IAM_TOKEN})

        with patch("qbraid.runtime.ibm.provider.urlopen", return_value=mock_resp):
            token = provider._exchange_api_key()

        assert token == FAKE_IAM_TOKEN

    def test_raises_on_missing_token(self):
        """Raises ValueError when no API key is available."""
        with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService"):
            p = QiskitRuntimeProvider(token="", channel="ibm_cloud")
            p.token = None
            p._runtime_service = MagicMock(spec=[])  # no _account attr

        with patch.object(QiskitRuntimeProvider, "_load_ibm_cloud_credentials", return_value={}):
            with pytest.raises(ValueError, match="IBM API key not found"):
                p._exchange_api_key()

    def test_raises_on_network_error(self, provider):
        """Raises ValueError on network failure."""
        from urllib.error import URLError

        with patch("qbraid.runtime.ibm.provider.urlopen", side_effect=URLError("timeout")):
            with pytest.raises(ValueError, match="Failed to exchange IBM API key"):
                provider._exchange_api_key()

    def test_raises_on_empty_access_token(self, provider, mock_ibm_api):
        """Raises ValueError when IAM returns no access_token."""
        mock_resp = mock_ibm_api({"token_type": "Bearer"})  # missing access_token

        with patch("qbraid.runtime.ibm.provider.urlopen", return_value=mock_resp):
            with pytest.raises(ValueError, match="No access_token"):
                provider._exchange_api_key()


# ---------------------------------------------------------------------------
# _ibm_api_get
# ---------------------------------------------------------------------------


class TestIbmApiGet:
    """Test authenticated GET requests to IBM Runtime API."""

    def test_makes_authenticated_request(self, provider, mock_ibm_api):
        """Request includes Bearer token, Service-CRN, and User-Agent."""
        mock_resp = mock_ibm_api({"jobs": [], "count": 0})

        with (
            patch.object(provider, "_exchange_api_key", return_value=FAKE_IAM_TOKEN),
            patch("qbraid.runtime.ibm.provider.urlopen", return_value=mock_resp) as mock_urlopen,
        ):
            provider._ibm_api_get("/jobs")

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert req.get_header("Authorization") == f"Bearer {FAKE_IAM_TOKEN}"
        assert req.get_header("Service-crn") == FAKE_INSTANCE
        assert "qbraid/" in req.get_header("User-agent")

    def test_appends_query_params(self, provider, mock_ibm_api):
        """Query params are URL-encoded."""
        mock_resp = mock_ibm_api({"jobs": []})

        with (
            patch.object(provider, "_exchange_api_key", return_value=FAKE_IAM_TOKEN),
            patch("qbraid.runtime.ibm.provider.urlopen", return_value=mock_resp) as mock_urlopen,
        ):
            provider._ibm_api_get("/jobs", params={"limit": 10, "pending": "true"})

        req = mock_urlopen.call_args[0][0]
        assert "limit=10" in req.full_url
        assert "pending=true" in req.full_url

    def test_appends_list_query_params_with_doseq(self, provider, mock_ibm_api):
        """List-valued params serialize as repeated params, not a bracketed repr."""
        mock_resp = mock_ibm_api({"jobs": []})

        with (
            patch.object(provider, "_exchange_api_key", return_value=FAKE_IAM_TOKEN),
            patch("qbraid.runtime.ibm.provider.urlopen", return_value=mock_resp) as mock_urlopen,
        ):
            provider._ibm_api_get("/jobs", params={"tags": ["alpha", "beta"]})

        url = mock_urlopen.call_args[0][0].full_url
        assert "tags=alpha" in url
        assert "tags=beta" in url
        # Guard against the pre-fix behavior where the list was stringified to
        # "['alpha', 'beta']" (URL-encoded "%5B..."), which IBM never matched.
        assert "%5B" not in url

    def test_raises_on_missing_instance(self):
        """Raises ValueError when CRN instance is not configured."""
        with patch("qbraid.runtime.ibm.provider.QiskitRuntimeService"):
            p = QiskitRuntimeProvider(token=FAKE_API_KEY, channel="ibm_cloud")
            p.token = FAKE_API_KEY
            p.instance = None
            p._runtime_service = MagicMock(spec=[])

        with (
            patch.object(p, "_exchange_api_key", return_value=FAKE_IAM_TOKEN),
            patch.object(QiskitRuntimeProvider, "_load_ibm_cloud_credentials", return_value={}),
        ):
            with pytest.raises(ValueError, match="instance.*not found"):
                p._ibm_api_get("/jobs")


# ---------------------------------------------------------------------------
# list_jobs
# ---------------------------------------------------------------------------


class TestListJobs:
    """Test list_jobs() for IBM Quantum REST API."""

    def test_list_all_jobs(self, provider):
        """List jobs with default params returns all jobs."""
        with patch.object(provider, "_ibm_api_get", return_value=IBM_JOBS_RESPONSE):
            result = provider.list_jobs()

        assert len(result["jobs"]) == 4
        assert result["count"] == 4

    def test_list_jobs_with_limit_and_offset(self, provider):
        """Limit and offset are passed to the API."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [IBM_JOB_SAMPLER], "count": 1}
        ) as mock_get:
            provider.list_jobs(limit=1, offset=2)

        call_args = mock_get.call_args
        params = call_args[1].get("params") or call_args[0][1]
        assert params["limit"] == 1
        assert params["offset"] == 2

    def test_list_pending_jobs(self, provider):
        """pending=True filters for queued/running jobs."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [IBM_JOB_QUEUED], "count": 1}
        ) as mock_get:
            result = provider.list_jobs(pending=True)

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert params["pending"] == "true"
        assert len(result["jobs"]) == 1

    def test_list_completed_jobs(self, provider):
        """pending=False filters for completed/failed/cancelled jobs."""
        with patch.object(
            provider,
            "_ibm_api_get",
            return_value={"jobs": [IBM_JOB_SAMPLER, IBM_JOB_FAILED], "count": 2},
        ) as mock_get:
            provider.list_jobs(pending=False)

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert params["pending"] == "false"

    def test_list_jobs_with_backend_filter(self, provider):
        """Backend filter is passed to API."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [IBM_JOB_SAMPLER], "count": 1}
        ) as mock_get:
            provider.list_jobs(backend="ibm_fez")

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert params["backend"] == "ibm_fez"

    def test_list_jobs_with_tags(self, provider):
        """Tags are passed to API."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [IBM_JOB_SAMPLER], "count": 1}
        ) as mock_get:
            provider.list_jobs(tags=["benchmark"])

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert params["tags"] == ["benchmark"]

    def test_list_jobs_with_date_range(self, provider):
        """Date range filters are passed to API."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [], "count": 0}
        ) as mock_get:
            provider.list_jobs(
                created_after="2026-04-01T00:00:00Z",
                created_before="2026-04-30T23:59:59Z",
            )

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert params["created_after"] == "2026-04-01T00:00:00Z"
        assert params["created_before"] == "2026-04-30T23:59:59Z"

    def test_list_jobs_omits_none_params(self, provider):
        """None-valued params are not sent to the API."""
        with patch.object(
            provider, "_ibm_api_get", return_value={"jobs": [], "count": 0}
        ) as mock_get:
            provider.list_jobs(backend=None, tags=None, pending=None)

        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert "backend" not in params
        assert "tags" not in params
        assert "pending" not in params


# ---------------------------------------------------------------------------
# get_job
# ---------------------------------------------------------------------------


class TestGetJob:
    """Test get_job() for single IBM job retrieval."""

    def test_get_job_returns_full_details(self, provider):
        """get_job returns the full job dict from the API."""
        with patch.object(provider, "_ibm_api_get", return_value=IBM_JOB_SAMPLER) as mock_get:
            result = provider.get_job("d5apdvonsj9s73b7th1g")

        mock_get.assert_called_once_with("/jobs/d5apdvonsj9s73b7th1g")
        assert result["id"] == "d5apdvonsj9s73b7th1g"
        assert result["backend"] == "ibm_fez"
        assert result["status"] == "Completed"
        assert result["program"]["id"] == "sampler"

    def test_get_job_estimator(self, provider):
        """get_job works for estimator jobs."""
        with patch.object(provider, "_ibm_api_get", return_value=IBM_JOB_ESTIMATOR):
            result = provider.get_job("e7bqfxrpwk0t84c9ui2h")

        assert result["program"]["id"] == "estimator"
        assert result["cost"] == 0.85


# ---------------------------------------------------------------------------
# End-to-end: handler-like usage
# ---------------------------------------------------------------------------


class TestEndToEndHandlerUsage:
    """
    Test list_jobs and get_job as they would be called from the
    JupyterLab extension's cloud_jobs.py handler.
    """

    def test_handler_list_ibm_jobs_flow(self, provider):
        """
        Simulate: CloudJobsIBMHandler.get() maps frontend status
        to IBM pending boolean, calls list_jobs, transforms results.
        """
        with patch.object(provider, "_ibm_api_get", return_value=IBM_JOBS_RESPONSE):
            # Frontend sends status="COMPLETED" → handler maps to pending=False
            result = provider.list_jobs(limit=10, pending=False)

        jobs = result["jobs"]
        # Transform to frontend shape (as the handler does)
        transformed = []
        for job in jobs:
            transformed.append(
                {
                    "id": job["id"],
                    "status": job["status"],
                    "backend": job["backend"],
                    "created": job.get("created"),
                    "cost": job.get("cost", 0),
                    "tags": job.get("tags", []),
                    "program": job.get("program", {}),
                }
            )

        serialized = json.dumps(
            {"status": "success", "jobs": transformed, "total": result["count"]}
        )
        parsed = json.loads(serialized)

        assert parsed["total"] == 4
        assert parsed["jobs"][0]["backend"] == "ibm_fez"

    def test_handler_get_ibm_result_flow(self, provider):
        """
        Simulate: CloudJobsIBMTaskHandler calls get_job to check status,
        then fetches result via _ibm_api_get.
        """
        with patch.object(provider, "_ibm_api_get") as mock_get:
            # First call: get job details
            mock_get.return_value = IBM_JOB_SAMPLER
            job = provider.get_job("d5apdvonsj9s73b7th1g")
            assert job["status"] == "Completed"

            # Second call: get metrics
            mock_get.return_value = IBM_METRICS
            metrics = provider._ibm_api_get("/jobs/d5apdvonsj9s73b7th1g/metrics")
            assert metrics["num_qubits"] == 40
            assert metrics["usage"]["quantum_seconds"] == 4.82

    def test_handler_ibm_backends_flow(self, provider):
        """
        Simulate: CloudJobsIBMBackendsHandler fetches backend list
        from IBM REST API.
        """
        backends_response = {
            "devices": [
                {"backend_name": "ibm_fez", "status": "active"},
                {"backend_name": "ibm_brisbane", "status": "active"},
                {"backend_name": "ibm_kyiv", "status": "active"},
            ]
        }

        with patch.object(provider, "_ibm_api_get", return_value=backends_response):
            result = provider._ibm_api_get("/backends")

        backend_names = [d["backend_name"] for d in result["devices"]]
        assert "ibm_fez" in backend_names
        assert len(backend_names) == 3

    def test_handler_status_mapping(self, provider):
        """
        Verify the status mapping logic used by the handler:
        frontend 'COMPLETED'/'FAILED' → pending=False
        frontend 'QUEUED'/'RUNNING' → pending=True
        frontend 'all'/None → pending=None (no filter)
        """
        completed_response = {"jobs": [IBM_JOB_SAMPLER, IBM_JOB_FAILED], "count": 2}
        pending_response = {"jobs": [IBM_JOB_QUEUED], "count": 1}
        all_response = IBM_JOBS_RESPONSE

        with patch.object(provider, "_ibm_api_get") as mock_get:
            # Completed/failed
            mock_get.return_value = completed_response
            provider.list_jobs(pending=False)
            params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
            assert params["pending"] == "false"

            # Queued/running
            mock_get.return_value = pending_response
            provider.list_jobs(pending=True)
            params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
            assert params["pending"] == "true"

            # All
            mock_get.return_value = all_response
            provider.list_jobs(pending=None)
            params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
            assert "pending" not in params


class TestApiErrorTyping:
    """The IBM REST paths must raise typed exceptions carrying the HTTP status.

    Consumers (e.g. qbraid-lab's cloud-jobs handlers) need to tell "this job does
    not exist" apart from "your credentials were rejected". Previously both
    collapsed into a bare ValueError, forcing callers to string-match the message
    — so a 404 for a nonexistent job ID was misreported as a credentials problem.
    """

    @staticmethod
    def _http_error(code):
        from urllib.error import HTTPError

        return HTTPError(
            url="https://quantum.cloud.ibm.com/api/v1/jobs/nope",
            code=code,
            msg={404: "Not Found", 401: "Unauthorized", 403: "Forbidden"}.get(code, "Error"),
            hdrs=None,
            fp=None,
        )

    @pytest.mark.parametrize(
        "code,expected",
        [
            (404, JobNotFoundError),
            (401, AuthorizationError),
            (403, AuthorizationError),
            (500, RuntimeAPIError),
        ],
    )
    def test_ibm_api_get_raises_typed_error(self, provider, code, expected):
        """Each HTTP status maps to its own exception type, with status_code set."""
        with (
            patch.object(provider, "_exchange_api_key", return_value="tok"),
            patch.object(
                provider, "instance", "crn:v1:bluemix:public:quantum-computing:us-east:a/x:y::"
            ),
            patch("qbraid.runtime.ibm.provider.urlopen", side_effect=self._http_error(code)),
        ):
            with pytest.raises(expected) as exc_info:
                provider._ibm_api_get("/jobs/nope")

        # Exact type, not just an instance: pytest.raises accepts subclasses, so
        # without this the 500 -> RuntimeAPIError row would pass even if the code
        # mis-mapped 500 to JobNotFoundError or AuthorizationError.
        assert type(exc_info.value) is expected
        assert exc_info.value.status_code == code

    def test_not_found_is_not_an_auth_error(self, provider):
        """A 404 must NOT be catchable as an authorization failure.

        This is the exact bug: a nonexistent job ID was surfacing credential
        guidance to users whose credentials were perfectly valid.
        """
        with (
            patch.object(provider, "_exchange_api_key", return_value="tok"),
            patch.object(
                provider, "instance", "crn:v1:bluemix:public:quantum-computing:us-east:a/x:y::"
            ),
            patch("qbraid.runtime.ibm.provider.urlopen", side_effect=self._http_error(404)),
        ):
            with pytest.raises(JobNotFoundError) as exc_info:
                provider._ibm_api_get("/jobs/nope")

        assert not isinstance(exc_info.value, AuthorizationError)
        assert isinstance(exc_info.value, ResourceNotFoundError)

    def test_typed_errors_remain_value_errors(self, provider):
        """Backwards compat: these paths used to raise ValueError."""
        with (
            patch.object(provider, "_exchange_api_key", return_value="tok"),
            patch.object(
                provider, "instance", "crn:v1:bluemix:public:quantum-computing:us-east:a/x:y::"
            ),
            patch("qbraid.runtime.ibm.provider.urlopen", side_effect=self._http_error(404)),
        ):
            with pytest.raises(ValueError):
                provider._ibm_api_get("/jobs/nope")

    def test_exchange_api_key_rejects_bad_key_as_auth_error(self, provider):
        """IAM rejecting the API key is a credentials problem, not a generic one."""
        with patch("qbraid.runtime.ibm.provider.urlopen", side_effect=self._http_error(401)):
            with pytest.raises(AuthorizationError) as exc_info:
                provider._exchange_api_key()

        assert exc_info.value.status_code == 401

    def test_exchange_api_key_server_error_is_not_an_auth_error(self, provider):
        """An IAM 500 is a transient service failure, not bad credentials."""
        with patch("qbraid.runtime.ibm.provider.urlopen", side_effect=self._http_error(500)):
            with pytest.raises(RuntimeAPIError) as exc_info:
                provider._exchange_api_key()

        assert not isinstance(exc_info.value, AuthorizationError)
        assert exc_info.value.status_code == 500

    def test_exchange_api_key_surfaces_iam_error_body(self, provider):
        """IAM's errorCode/errorMessage say WHY the key was rejected; keep them.

        Regression: a 400 was formatted as just "HTTP Error 400: Bad Request",
        discarding the body that distinguishes an invalid/mis-copied key
        (BXNIM0415E) from an empty one (BXNIM0109E) or a suspended account.
        """
        body = json.dumps(
            {
                "errorCode": "BXNIM0415E",
                "errorMessage": "Provided API key could not be found.",
                "context": {"requestId": "req-iam-42"},
            }
        ).encode("utf-8")
        error = HTTPError(
            "https://iam.cloud.ibm.com/identity/token", 400, "Bad Request", None, BytesIO(body)
        )

        with patch("qbraid.runtime.ibm.provider.urlopen", side_effect=error):
            with pytest.raises(
                AuthorizationError, match="BXNIM0415E.*could not be found"
            ) as exc_info:
                provider._exchange_api_key()

        assert exc_info.value.status_code == 400
        assert exc_info.value.error_code == "BXNIM0415E"
        assert exc_info.value.trace == "req-iam-42"

    def test_ibm_api_get_network_error_has_no_status_code(self, provider):
        """A transport failure has no HTTP response, so status_code stays None."""
        from urllib.error import URLError

        with (
            patch.object(provider, "_exchange_api_key", return_value="tok"),
            patch.object(
                provider, "instance", "crn:v1:bluemix:public:quantum-computing:us-east:a/x:y::"
            ),
            patch("qbraid.runtime.ibm.provider.urlopen", side_effect=URLError("timeout")),
        ):
            with pytest.raises(RuntimeAPIError) as exc_info:
                provider._ibm_api_get("/jobs")

        assert exc_info.value.status_code is None
        assert not isinstance(exc_info.value, (AuthorizationError, JobNotFoundError))


class TestIbmErrorBody:
    """IBM returns a structured ErrorContainer body alongside the HTTP status.

    Responses captured live from us-east.quantum-computing.cloud.ibm.com:

      404 (bad job id)  -> {"errors": [{"code": 1291, "message": "Job not found..."}],
                            "trace": "..."}
      403 (bad CRN)     -> {"errors": [{"code": 1200, "message": "You are not authorized..."}],
                            "trace": "..."}

    An edge proxy in front of the API (e.g. rejecting a blocked User-Agent) also answers
    403, but with an HTML block page instead of an ErrorContainer. That is not a
    credentials failure and must not be reported as one -- doing so would tell users with
    perfectly valid credentials to go re-save them, which is the bug this PR exists to fix.
    """

    WAF_BLOCK_PAGE = b"<!DOCTYPE html>\n<html><body>Access denied</body></html>"
    MORE_INFO = "https://cloud.ibm.com/apidocs/quantum-computing#error-handling"

    @staticmethod
    def _http_error(code, body: Optional[bytes]):
        return HTTPError(
            url="https://us-east.quantum-computing.cloud.ibm.com/jobs",
            code=code,
            msg="Error",
            hdrs=None,
            fp=None if body is None else BytesIO(body),
        )

    @staticmethod
    def _error_container(code, message, solution="Verify the job ID.", more_info=MORE_INFO):
        """An ErrorContainer body. `code` is an int, as IBM actually sends it."""
        return json.dumps(
            {
                "errors": [
                    {
                        "code": code,
                        "message": message,
                        "solution": solution,
                        "more_info": more_info,
                    }
                ],
                "trace": "c4dd86aa-1150-485e-85f3-2e4e5f410317",
            }
        ).encode()

    def _get(self, provider, error):
        """Run _ibm_api_get against a mocked HTTPError and return the raised exception."""
        with (
            patch.object(provider, "_exchange_api_key", return_value="tok"),
            patch.object(
                provider, "instance", "crn:v1:bluemix:public:quantum-computing:us-east:a/x:y::"
            ),
            patch("qbraid.runtime.ibm.provider.urlopen", side_effect=error),
        ):
            with pytest.raises(RuntimeAPIError) as exc_info:
                provider._ibm_api_get("/jobs")
        return exc_info.value

    def test_ibm_error_code_and_trace_are_captured(self, provider):
        """IBM's own error code and request trace ride along on the exception."""
        body = self._error_container(1291, "Job not found. Job ID: deadbeef")
        err = self._get(provider, self._http_error(404, body))

        assert type(err) is JobNotFoundError
        assert err.status_code == 404
        # IBM's spec declares `code` a string but sends an int -- normalize.
        assert err.error_code == "1291"
        assert err.trace == "c4dd86aa-1150-485e-85f3-2e4e5f410317"
        assert "Job not found" in str(err)

    def test_forbidden_with_ibm_body_is_an_auth_error(self, provider):
        """A 403 that IBM itself produced is a genuine authorization failure."""
        body = self._error_container(1200, "You are not authorized to perform this action.")
        err = self._get(provider, self._http_error(403, body))

        assert type(err) is AuthorizationError
        assert err.status_code == 403
        assert err.error_code == "1200"

    def test_forbidden_from_edge_proxy_is_not_an_auth_error(self, provider):
        """A 403 with an HTML body did not come from IBM's API.

        The credentials may be perfectly valid -- the request was blocked upstream.
        Reporting this as AuthorizationError sends users to re-save working credentials.
        """
        err = self._get(provider, self._http_error(403, self.WAF_BLOCK_PAGE))

        assert type(err) is RuntimeAPIError
        assert not isinstance(err, AuthorizationError)
        assert err.status_code == 403
        assert err.error_code is None
        assert err.trace is None

    def test_bodyless_error_falls_back_to_status_mapping(self, provider):
        """With no body at all we have nothing better to go on than the status."""
        err = self._get(provider, self._http_error(401, None))

        assert type(err) is AuthorizationError
        assert err.status_code == 401
        assert err.error_code is None

    def test_unreadable_body_falls_back_to_status_mapping(self, provider):
        """A body that raises on read() is treated as no body at all.

        A real HTTPError's stream can be closed or already consumed by the time it
        is inspected, in which case read() raises instead of returning bytes.
        """
        http_error = self._http_error(401, None)
        with patch.object(http_error, "read", side_effect=OSError("stream closed")):
            err = self._get(provider, http_error)

        assert type(err) is AuthorizationError
        assert err.status_code == 401
        assert err.error_code is None

    def test_malformed_json_body_is_not_an_auth_error(self, provider):
        """A body that is present but unparseable is treated like any other foreign body."""
        err = self._get(provider, self._http_error(403, b'{"truncated": '))

        assert type(err) is RuntimeAPIError
        assert err.status_code == 403

    def test_solution_and_more_info_are_captured(self, provider):
        """IBM ships user-facing remediation text with every error; keep it.

        Captured live from a 404: the `solution` field is exactly the guidance a UI
        wants to show, and it is authored by the party that knows why the call failed.
        Note `solution` is NOT declared in IBM's OpenAPI schema, so it is optional.
        """
        solution = "Verify the job ID is correct and that you have the correct access permissions."
        body = self._error_container(1291, "Job not found. Job ID: deadbeef", solution=solution)
        err = self._get(provider, self._http_error(404, body))

        assert err.solution == solution
        assert err.more_info == self.MORE_INFO

    def test_missing_solution_is_none_not_an_error(self, provider):
        """`solution` is undeclared in IBM's schema, so it may simply not be there."""
        body = json.dumps({"errors": [{"code": 1291, "message": "Job not found."}]}).encode()
        err = self._get(provider, self._http_error(404, body))

        assert type(err) is JobNotFoundError
        assert err.error_code == "1291"
        assert err.solution is None
        assert err.more_info is None
        assert err.trace is None

    def test_closed_stream_is_treated_as_no_body(self, provider):
        """A body stream that is already closed must degrade to status-only mapping.

        read() on a closed stream raises ValueError, which previously escaped the
        parser and masked the original HTTP error entirely.
        """
        http_error = self._http_error(403, b'{"errors": [{"code": 1200}]}')
        http_error.fp.close()
        err = self._get(provider, http_error)

        # No readable body -> (False, None) -> a 403 maps to AuthorizationError.
        assert type(err) is AuthorizationError
        assert err.status_code == 403
        assert err.error_code is None


class TestParseIamError:
    """IAM error-body extraction fallbacks (the happy path is covered above)."""

    @staticmethod
    def _http_error(body: Optional[bytes]) -> HTTPError:
        fp = None if body is None else BytesIO(body)
        return HTTPError("https://iam.cloud.ibm.com/identity/token", 400, "Bad Request", None, fp)

    def test_non_json_body_surfaced_raw_and_truncated(self):
        """A non-JSON body (e.g. an HTML error page) is kept, capped at 500 chars."""
        detail = _parse_iam_error(self._http_error(b"<html>Service unavailable</html>" * 100))

        assert detail is not None
        assert detail.message.startswith("<html>")
        assert len(detail.message) <= 500
        assert detail.error_code is None

    def test_unrecognized_json_shape_surfaced_raw(self):
        """JSON that is not IAM's error shape is kept as-is."""
        detail = _parse_iam_error(self._http_error(b'{"detail": "something else"}'))

        assert detail is not None
        assert '"detail": "something else"' in detail.message

    def test_empty_body_is_none(self):
        assert _parse_iam_error(self._http_error(b"")) is None

    def test_missing_body_is_none(self):
        assert _parse_iam_error(self._http_error(None)) is None

    def test_closed_stream_is_none(self):
        error = self._http_error(b'{"errorCode": "BXNIM0415E"}')
        error.fp.close()
        assert _parse_iam_error(error) is None
