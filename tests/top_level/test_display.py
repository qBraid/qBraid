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
Unit tests for ipython and other display functions.

"""
import logging
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from qbraid._display import running_in_jupyter
from qbraid.programs.exceptions import PackageValueError
from qbraid.runtime._display import _job_table_jupyter
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.native.provider import QbraidProvider

# pylint: disable=missing-function-docstring,redefined-outer-name

MOCK_JOB_DATA = [
    {
        "shots": 100,
        "circuitNumQubits": 1,
        "qbraidDeviceId": "aws_dm_sim",
        "vendorDeviceId": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
        "qbraidJobId": "aws_dm_sim-jovyan-qjob-1234567890",
        "status": "COMPLETED",
        "qbraidStatus": "COMPLETED",
        "vendor": "aws",
        "provider": "aws",
        "tags": {"test": "123"},
        "createdAt": "2024-04-30T17:28:38.962Z",
        "updatedAt": "2024-04-30T17:28:38.962Z",
    },
    {
        "shots": 100,
        "circuitNumQubits": 3,
        "qbraidDeviceId": "ibm_q_oslo",
        "vendorDeviceId": "ibm_oslo",
        "qbraidJobId": "ibm_q_oslo-jovyan-qjob-1234567890",
        "status": "COMPLETED",
        "qbraidStatus": "COMPLETED",
        "vendor": "ibm",
        "provider": "ibm",
        "tags": {"test": "*"},
        "createdAt": "2024-04-30T17:28:48.502Z",
        "updatedAt": "2024-04-30T17:28:48.502Z",
    },
]


class MockQbraidClient:
    """Mock QbraidClient class for testing"""

    def search_jobs(self, query: dict):
        """Mock search_jobs method."""
        max_results = query.get("resultsPerPage", 10)
        tag = query.get("tags.test", None)
        device_id = query.get("qbraidDeviceId", None)
        provider = query.get("provider", None)

        jobs = MOCK_JOB_DATA

        if device_id:
            jobs = [job for job in jobs if job["qbraidDeviceId"] == device_id]

        if provider:
            jobs = [job for job in jobs if job["provider"] == provider]

        if tag:
            tags = {"test": tag}

            jobs = [
                job
                for job in jobs
                if any(job["tags"].get(key) == value for key, value in tags.items())
            ]

        if max_results < len(jobs):
            return jobs[:max_results]
        return jobs


@pytest.fixture
def mock_provider():
    """Mock QbraidProvider class for testing."""
    return QbraidProvider(client=MockQbraidClient())


@pytest.fixture
def job_data():
    """Fixture to provide preprocessed job data."""
    JOB_STATUS_LIST = [status.name for status in JobStatus]
    data = [
        (f"job_{index}", f"timestamp_{index}", value) for index, value in enumerate(JOB_STATUS_LIST)
    ]
    yield data


class MockIPython:
    """Mock IPython class for testing."""

    def __init__(self, kernel):
        self.kernel = kernel


@pytest.fixture
def mock_ipython(request):
    """Fixture to mock IPython in sys.modules and restore it after the test."""
    kernel_value = request.param
    original_ipython = sys.modules.get("IPython", None)  # Save the original IPython module
    # Create a mock module and assign get_ipython
    mock_module = type("MockModule", (), {})()  # Create a mock module object
    mock_module.get_ipython = Mock(return_value=MockIPython(kernel_value))
    sys.modules["IPython"] = mock_module  # Set the mock module in sys.modules

    yield  # Yield control to the test function

    # Restore the original state after the test
    if original_ipython is not None:
        sys.modules["IPython"] = original_ipython
    else:
        del sys.modules["IPython"]


def test_package_value_error():
    """Test raising PackageValueError exception."""
    with pytest.raises(PackageValueError):
        raise PackageValueError("custom msg")


def test_running_in_jupyter():
    """Test ``running_in_jupyter`` for non-jupyter environment."""
    assert not running_in_jupyter()


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_ipython_imported_but_ipython_none(mock_ipython):
    """Test ``running_in_jupyter`` for IPython imported but ``get_ipython()`` returns None."""
    assert not running_in_jupyter()


@pytest.mark.parametrize("mock_ipython", ["non-empty kernel"], indirect=True)
def test_ipython_imported_and_in_jupyter(mock_ipython):
    """Test ``running_in_jupyter`` for IPython imported and in Jupyter."""
    assert running_in_jupyter()


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_get_jobs_no_results(capfd, mock_provider, mock_ipython):
    """Test ``get_jobs`` stdout for results == 0.
    When no results are found, a single line is printed.
    """
    mock_provider.display_jobs(device_id="non-existent-device", status="ONLINE")
    out, err = capfd.readouterr()
    assert out == "No jobs found matching given criteria\n"
    assert len(err) == 0


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_get_aws_jobs_by_tag(capfd, mock_provider, mock_ipython):
    """Test ``get_jobs`` for aws tagged jobs."""
    mock_provider.display_jobs(tags={"test": "123"}, provider="aws", max_results=1)
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert MOCK_JOB_DATA[0]["qbraidJobId"] in out
    assert len(err) == 0


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_get_ibm_jobs_by_tag(capfd, mock_provider, mock_ipython):
    """Test ``get_jobs`` for ibm tagged jobs."""
    mock_provider.display_jobs(tags={"test": "*"}, provider="ibm", max_results=1)
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert MOCK_JOB_DATA[1]["qbraidJobId"] in out
    assert len(err) == 0


@pytest.mark.parametrize("mock_ipython", [None], indirect=True)
def test_get_jobs_results(capfd, mock_provider, mock_ipython):
    """Test ``get_jobs`` stdout for results > 0.
    When results returned, output format is as follows:
    (1) Message
    (2) Empty line
    (3) Section titles
    (4) Underline titles
    (4+x) ``x`` lines of results
    (5+x) Empty line

    So, for ``numResults == x`` we expected ``6+x`` total lines from stdout.
    """
    num_results = 2  # test value
    lines_expected = 5 + num_results
    mock_provider.display_jobs(max_results=num_results)
    out, err = capfd.readouterr()
    lines_out = len(out.split("\n"))
    assert lines_out == lines_expected
    assert len(err) == 0


@pytest.mark.parametrize("mock_ipython", ["non-empty kernel"], indirect=True)
def test_display_jobs_in_jupyter(capfd, job_data, mock_ipython):
    """Test ``_display_jobs_jupyter`` stdout for non-empty job status list."""
    msg = "test123"
    _job_table_jupyter(job_data, msg)
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


@pytest.mark.parametrize("mock_ipython", ["non-empty kernel"], indirect=True)
def test_get_jobs_in_jupyter(capfd, mock_provider, mock_ipython):
    """Test `get_jobs` stdout for non-empty kernel.
    When running in Jupyter, the output should be an HTML object."""
    mock_provider.display_jobs()  # Assuming this uses IPython.get_ipython internally
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


def test_running_in_jupyter_logs_exception(caplog):
    """
    Test that an exception raised in running_in_jupyter() is logged correctly.
    """
    with patch("sys.modules", new_callable=lambda: {"IPython": MagicMock()}):
        sys.modules["IPython"].__dict__["get_ipython"] = MagicMock(
            side_effect=Exception("Test exception")
        )

        caplog.set_level(logging.ERROR)

        result = running_in_jupyter()

        assert not result, "running_in_jupyter() should return False when an exception occurs"
        assert (
            "Error checking if running in Jupyter: Test exception" in caplog.text
        ), "The exception should be logged as an error"
