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
Unit tests for BraketProvider job listing and retrieval.

Tests list_jobs(), get_job(), _search_tasks(), and _serialize_task()
using realistic mock data modeled after actual AWS Braket API responses.
"""

import datetime
from unittest.mock import MagicMock, patch

import pytest

from qbraid.runtime.aws.provider import BraketProvider

# ---------------------------------------------------------------------------
# Realistic mock data — modeled after real AWS Braket task responses
# ---------------------------------------------------------------------------

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
IONQ_ARIA_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1"
AQUILA_ARN = "arn:aws:braket:us-east-1::device/qpu/quera/Aquila"
IQM_GARNET_ARN = "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet"

TASK_1 = {
    "quantumTaskArn": "arn:aws:braket:us-east-1:592242689881:quantum-task/abc12345-1111-2222-3333-444455556666",
    "status": "COMPLETED",
    "deviceArn": SV1_ARN,
    "shots": 1000,
    "outputS3Bucket": "amazon-braket-us-east-1-592242689881",
    "outputS3Directory": "tasks/abc12345-1111-2222-3333-444455556666",
    "createdAt": datetime.datetime(2026, 4, 14, 20, 53, 56),
    "endedAt": datetime.datetime(2026, 4, 14, 20, 54, 19),
    "tags": {"project": "bell-test", "user": "ryanhill"},
}

TASK_2 = {
    "quantumTaskArn": "arn:aws:braket:us-east-1:592242689881:quantum-task/def67890-aaaa-bbbb-cccc-ddddeeeeffff",
    "status": "COMPLETED",
    "deviceArn": IONQ_ARIA_ARN,
    "shots": 100,
    "outputS3Bucket": "amazon-braket-us-east-1-592242689881",
    "outputS3Directory": "tasks/def67890-aaaa-bbbb-cccc-ddddeeeeffff",
    "createdAt": datetime.datetime(2026, 4, 15, 10, 0, 0),
    "endedAt": datetime.datetime(2026, 4, 15, 10, 2, 30),
    "tags": {},
}

TASK_3_AQUILA = {
    "quantumTaskArn": "arn:aws:braket:us-east-1:592242689881:quantum-task/ahs99999-1111-2222-3333-aquila000000",
    "status": "COMPLETED",
    "deviceArn": AQUILA_ARN,
    "shots": 100,
    "outputS3Bucket": "amazon-braket-us-east-1-592242689881",
    "outputS3Directory": "tasks/ahs99999-1111-2222-3333-aquila000000",
    "createdAt": datetime.datetime(2026, 4, 20, 22, 43, 24),
    "endedAt": datetime.datetime(2026, 4, 20, 23, 15, 28),
    "tags": {"experiment": "ahs-lattice"},
}

TASK_4_EU = {
    "quantumTaskArn": "arn:aws:braket:eu-north-1:592242689881:quantum-task/eu112233-4455-6677-8899-aabbccddeeff",
    "status": "RUNNING",
    "deviceArn": IQM_GARNET_ARN,
    "shots": 500,
    "outputS3Bucket": "amazon-braket-eu-north-1-592242689881",
    "outputS3Directory": "tasks/eu112233-4455-6677-8899-aabbccddeeff",
    "createdAt": datetime.datetime(2026, 4, 25, 8, 56, 10),
    "endedAt": None,
    "tags": {},
}

TASK_1_FULL = {
    **TASK_1,
    "failureReason": None,
    "deviceParameters": '{"paradigmParameters": {"qubitCount": 2}}',
    "jobArn": None,
    "associations": [],
    "ResponseMetadata": {"RequestId": "abc123", "HTTPStatusCode": 200},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider():
    """BraketProvider with mocked credentials."""
    with patch.object(BraketProvider, "__init__", lambda self, **kw: None):
        p = BraketProvider.__new__(BraketProvider)
        p.aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
        p.aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        p.aws_session_token = None
        return p


@pytest.fixture
def mock_braket_client():
    """Mock boto3 braket client."""
    return MagicMock()


@pytest.fixture
def mock_aws_session(mock_braket_client):
    """Mock AwsSession with a braket client attached."""
    session = MagicMock()
    session.boto_session.client.return_value = mock_braket_client
    return session


# ---------------------------------------------------------------------------
# _serialize_task
# ---------------------------------------------------------------------------


class TestSerializeTask:
    """Test datetime serialization for JSON compatibility."""

    def test_converts_datetime_to_iso(self):
        task = {
            "quantumTaskArn": "arn:aws:braket:us-east-1:123:quantum-task/abc",
            "status": "COMPLETED",
            "createdAt": datetime.datetime(2026, 4, 14, 20, 53, 56),
            "endedAt": datetime.datetime(2026, 4, 14, 20, 54, 19),
        }
        result = BraketProvider._serialize_task(task)
        assert result["createdAt"] == "2026-04-14T20:53:56"
        assert result["endedAt"] == "2026-04-14T20:54:19"
        assert result["status"] == "COMPLETED"

    def test_preserves_non_datetime_values(self):
        task = {
            "quantumTaskArn": "arn:aws:braket:us-east-1:123:quantum-task/abc",
            "status": "FAILED",
            "shots": 1000,
            "tags": {"env": "test"},
            "endedAt": None,
        }
        result = BraketProvider._serialize_task(task)
        assert result["shots"] == 1000
        assert result["tags"] == {"env": "test"}
        assert result["endedAt"] is None


# ---------------------------------------------------------------------------
# list_jobs — single device / no filter
# ---------------------------------------------------------------------------


class TestListJobs:
    """Test list_jobs() for various filtering and pagination scenarios."""

    def test_list_jobs_no_filters(self, provider, mock_aws_session, mock_braket_client):
        """List jobs with no filters returns all tasks from default region."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_1, TASK_2],
            "nextToken": None,
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs()

        assert len(result["tasks"]) == 2
        assert result["nextToken"] is None
        # Verify datetimes were serialized
        assert isinstance(result["tasks"][0]["createdAt"], str)

        mock_braket_client.search_quantum_tasks.assert_called_once_with(
            maxResults=20, filters=[]
        )

    def test_list_jobs_with_status_filter(self, provider, mock_aws_session, mock_braket_client):
        """Filter by status passes the correct filter to boto3."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_1],
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(status="COMPLETED")

        assert len(result["tasks"]) == 1
        call_kwargs = mock_braket_client.search_quantum_tasks.call_args[1]
        assert {"name": "status", "operator": "EQUAL", "values": ["COMPLETED"]} in call_kwargs["filters"]

    def test_list_jobs_with_device_filter(self, provider, mock_aws_session, mock_braket_client):
        """Filter by device ARN passes the correct filter."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_2],
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(device_arn=IONQ_ARIA_ARN)

        call_kwargs = mock_braket_client.search_quantum_tasks.call_args[1]
        filters = call_kwargs["filters"]
        assert {"name": "deviceArn", "operator": "EQUAL", "values": [IONQ_ARIA_ARN]} in filters

    def test_list_jobs_with_status_and_device(self, provider, mock_aws_session, mock_braket_client):
        """Combined status + device filter produces two filter entries."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [],
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(status="FAILED", device_arn=SV1_ARN)

        call_kwargs = mock_braket_client.search_quantum_tasks.call_args[1]
        assert len(call_kwargs["filters"]) == 2
        assert result["tasks"] == []

    def test_list_jobs_with_pagination(self, provider, mock_aws_session, mock_braket_client):
        """Pagination token is passed through and returned."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_2],
            "nextToken": "page2_token_xyz",
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(next_token="page1_token_abc", limit=1)

        assert result["nextToken"] == "page2_token_xyz"
        call_kwargs = mock_braket_client.search_quantum_tasks.call_args[1]
        assert call_kwargs["nextToken"] == "page1_token_abc"
        assert call_kwargs["maxResults"] == 1

    def test_list_jobs_custom_limit(self, provider, mock_aws_session, mock_braket_client):
        """Custom limit is passed to search_quantum_tasks."""
        mock_braket_client.search_quantum_tasks.return_value = {"quantumTasks": []}

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            provider.list_jobs(limit=50)

        call_kwargs = mock_braket_client.search_quantum_tasks.call_args[1]
        assert call_kwargs["maxResults"] == 50


# ---------------------------------------------------------------------------
# list_jobs — multi-device (cross-region)
# ---------------------------------------------------------------------------


class TestListJobsMultiDevice:
    """Test list_jobs() with device_arns for cross-region queries."""

    def test_multi_device_queries_each_arn(self, provider):
        """device_arns queries each ARN in its extracted region and merges results."""
        call_count = 0

        def mock_search_tasks(region, limit, status=None, device_arn=None):
            nonlocal call_count
            call_count += 1
            if device_arn == IONQ_ARIA_ARN:
                return {"tasks": [BraketProvider._serialize_task(TASK_2)]}
            elif device_arn == IQM_GARNET_ARN:
                return {"tasks": [BraketProvider._serialize_task(TASK_4_EU)]}
            return {"tasks": []}

        with patch.object(provider, "_search_tasks", side_effect=mock_search_tasks), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(device_arns=[IONQ_ARIA_ARN, IQM_GARNET_ARN])

        assert call_count == 2
        assert len(result["tasks"]) == 2
        assert result["nextToken"] is None  # pagination disabled for multi-device

    def test_multi_device_sorts_by_created_descending(self, provider):
        """Merged results are sorted by createdAt descending."""
        older = BraketProvider._serialize_task(TASK_1)  # Apr 14
        newer = BraketProvider._serialize_task(TASK_2)  # Apr 15

        def mock_search_tasks(region, limit, status=None, device_arn=None):
            if device_arn == SV1_ARN:
                return {"tasks": [older]}
            return {"tasks": [newer]}

        with patch.object(provider, "_search_tasks", side_effect=mock_search_tasks), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(device_arns=[SV1_ARN, IONQ_ARIA_ARN])

        assert result["tasks"][0]["createdAt"] > result["tasks"][1]["createdAt"]

    def test_multi_device_respects_limit(self, provider):
        """Merged results are trimmed to the requested limit."""
        tasks = [
            BraketProvider._serialize_task({
                **TASK_1,
                "quantumTaskArn": f"arn:aws:braket:us-east-1:123:quantum-task/task-{i}",
                "createdAt": datetime.datetime(2026, 4, 14 + i, 12, 0, 0),
            })
            for i in range(5)
        ]

        def mock_search_tasks(region, limit, status=None, device_arn=None):
            return {"tasks": tasks}

        with patch.object(provider, "_search_tasks", side_effect=mock_search_tasks), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(device_arns=[SV1_ARN], limit=3)

        assert len(result["tasks"]) == 3

    def test_multi_device_extracts_region_from_arn(self, provider):
        """Regions are correctly extracted from device ARNs."""
        regions_queried = []

        def mock_search_tasks(region, limit, status=None, device_arn=None):
            regions_queried.append(region)
            return {"tasks": []}

        with patch.object(provider, "_search_tasks", side_effect=mock_search_tasks), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            provider.list_jobs(device_arns=[IONQ_ARIA_ARN, IQM_GARNET_ARN])

        assert "us-east-1" in regions_queried
        assert "eu-north-1" in regions_queried

    def test_multi_device_with_status_filter(self, provider):
        """Status filter is passed through to each per-device query."""
        statuses_passed = []

        def mock_search_tasks(region, limit, status=None, device_arn=None):
            statuses_passed.append(status)
            return {"tasks": []}

        with patch.object(provider, "_search_tasks", side_effect=mock_search_tasks), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            provider.list_jobs(device_arns=[SV1_ARN, IONQ_ARIA_ARN], status="COMPLETED")

        assert all(s == "COMPLETED" for s in statuses_passed)


# ---------------------------------------------------------------------------
# list_jobs — tag filtering
# ---------------------------------------------------------------------------


class TestListJobsTagFilter:
    """Test list_jobs() with tag-based filtering."""

    def test_tag_filter_narrows_results(self, provider, mock_aws_session, mock_braket_client):
        """Only tasks matching the tag ARNs are returned."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_1, TASK_2],
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"), \
             patch.object(provider, "get_tasks_by_tag", return_value=[TASK_1["quantumTaskArn"]]):
            result = provider.list_jobs(tags={"project": "bell-test"})

        # Only TASK_1 has the matching tag ARN
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["quantumTaskArn"] == TASK_1["quantumTaskArn"]

    def test_multiple_tags_intersect(self, provider, mock_aws_session, mock_braket_client):
        """Multiple tags are AND-ed together."""
        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_1, TASK_2, TASK_3_AQUILA],
        }

        call_count = [0]

        def mock_get_tasks_by_tag(key, values=None, region_names=None):
            call_count[0] += 1
            if key == "project":
                return [TASK_1["quantumTaskArn"], TASK_3_AQUILA["quantumTaskArn"]]
            elif key == "user":
                return [TASK_1["quantumTaskArn"]]
            return []

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"), \
             patch.object(provider, "get_tasks_by_tag", side_effect=mock_get_tasks_by_tag):
            result = provider.list_jobs(tags={"project": "bell-test", "user": "ryanhill"})

        assert call_count[0] == 2
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["quantumTaskArn"] == TASK_1["quantumTaskArn"]


# ---------------------------------------------------------------------------
# get_job
# ---------------------------------------------------------------------------


class TestGetJob:
    """Test get_job() for single task retrieval."""

    def test_get_job_returns_serialized_task(self, provider, mock_aws_session, mock_braket_client):
        """get_job returns a fully serialized task dict."""
        mock_braket_client.get_quantum_task.return_value = TASK_1_FULL

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session):
            result = provider.get_job(TASK_1["quantumTaskArn"])

        assert result["status"] == "COMPLETED"
        assert isinstance(result["createdAt"], str)
        assert result["shots"] == 1000
        mock_braket_client.get_quantum_task.assert_called_once_with(
            quantumTaskArn=TASK_1["quantumTaskArn"]
        )

    def test_get_job_extracts_region_from_arn(self, provider):
        """Region is parsed from the task ARN."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.boto_session.client.return_value = mock_client
        mock_client.get_quantum_task.return_value = {
            "quantumTaskArn": TASK_4_EU["quantumTaskArn"],
            "status": "RUNNING",
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_session) as mock_get_session:
            provider.get_job(TASK_4_EU["quantumTaskArn"])

        mock_get_session.assert_called_once_with(region_name="eu-north-1")

    def test_get_job_falls_back_to_default_region(self, provider):
        """Malformed ARN falls back to default region."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.boto_session.client.return_value = mock_client
        mock_client.get_quantum_task.return_value = {"status": "COMPLETED"}

        with patch.object(provider, "_get_aws_session", return_value=mock_session), \
             patch.object(provider, "_get_default_region", return_value="us-west-2"):
            provider.get_job("malformed-arn")

        mock_session.boto_session.client.assert_called_with("braket", region_name="us-west-2")


# ---------------------------------------------------------------------------
# End-to-end: handler-like usage
# ---------------------------------------------------------------------------


class TestEndToEndHandlerUsage:
    """
    Test list_jobs and get_job as they would be called from the
    JupyterLab extension's cloud_jobs.py handler.
    """

    def test_handler_list_jobs_flow(self, provider, mock_aws_session, mock_braket_client):
        """
        Simulate: CloudJobsAWSHandler.get() calls list_jobs() then
        serializes to JSON for the frontend.
        """
        import json

        mock_braket_client.search_quantum_tasks.return_value = {
            "quantumTasks": [TASK_1, TASK_3_AQUILA],
            "nextToken": "next_page_abc",
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_aws_session), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(limit=10, status="COMPLETED")

        # Handler serializes to JSON
        response = {
            "status": "success",
            "jobs": result["tasks"],
            "nextToken": result["nextToken"],
        }
        serialized = json.dumps(response)
        parsed = json.loads(serialized)

        assert len(parsed["jobs"]) == 2
        assert parsed["nextToken"] == "next_page_abc"
        assert parsed["jobs"][0]["shots"] == 1000
        assert parsed["jobs"][1]["deviceArn"] == AQUILA_ARN

    def test_handler_get_job_result_flow(self, provider):
        """
        Simulate: CloudJobsAWSTaskHandler fetches task metadata to get
        S3 output location, then the handler fetches result from S3.
        """
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.boto_session.client.return_value = mock_client
        mock_client.get_quantum_task.return_value = {
            **TASK_1_FULL,
            "outputS3Bucket": "amazon-braket-us-east-1-592242689881",
            "outputS3Directory": "tasks/abc12345-1111-2222-3333-444455556666",
        }

        with patch.object(provider, "_get_aws_session", return_value=mock_session):
            task = provider.get_job(TASK_1["quantumTaskArn"])

        assert task["outputS3Bucket"] == "amazon-braket-us-east-1-592242689881"
        assert "outputS3Directory" in task

    def test_handler_multi_device_filter_flow(self, provider):
        """
        Simulate: CloudJobsAWSHandler receives device_arn filter with
        multiple ARNs from the frontend device selector.
        """
        sv1_task = BraketProvider._serialize_task(TASK_1)
        ionq_task = BraketProvider._serialize_task(TASK_2)

        def mock_search(region, limit, status=None, device_arn=None):
            if device_arn == SV1_ARN:
                return {"tasks": [sv1_task]}
            elif device_arn == IONQ_ARIA_ARN:
                return {"tasks": [ionq_task]}
            return {"tasks": []}

        with patch.object(provider, "_search_tasks", side_effect=mock_search), \
             patch.object(provider, "_get_default_region", return_value="us-east-1"):
            result = provider.list_jobs(
                device_arns=[SV1_ARN, IONQ_ARIA_ARN],
                limit=10,
            )

        assert len(result["tasks"]) == 2
        arns = {t["quantumTaskArn"] for t in result["tasks"]}
        assert TASK_1["quantumTaskArn"] in arns
        assert TASK_2["quantumTaskArn"] in arns
