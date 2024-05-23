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
Unit tests for qbraid top-level functionality

"""
import os
import sys
from unittest.mock import Mock, patch

import pytest
from qbraid_core.services.quantum import QuantumClient

from qbraid import __version__
from qbraid._display import running_in_jupyter
from qbraid.interface.random import random_circuit
from qbraid.programs.exceptions import PackageValueError
from qbraid.runtime._display import _job_table_jupyter
from qbraid.runtime.native.provider import QbraidProvider

# pylint: disable=missing-function-docstring,redefined-outer-name

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid/AWS/IBM storage)"

jobs_state_libs = QuantumClient.qbraid_jobs_state().get("libs", {})
braket_enabled = jobs_state_libs.get("braket", {}).get("enabled", False)
qiskit_enabled = jobs_state_libs.get("qiskit", {}).get("enabled", False)

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


class MockQbraidClient(Mock):

    def search_jobs(self, query: dict):
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


job_status_list = [
    "INITIALIZING",
    "QUEUED",
    "VALIDATING",
    "RUNNING",
    "CANCELLING",
    "CANCELLED",
    "COMPLETED",
    "FAILED",
    "UNKNOWN",
]


def test_package_value_error():
    """Test raising PackageValueError exception."""
    with pytest.raises(PackageValueError):
        raise PackageValueError("custom msg")


def test_running_in_jupyter():
    """Test ``running_in_jupyter`` for non-jupyter environment."""
    assert not running_in_jupyter()


def test_ipython_imported_but_ipython_none():
    """Test ``running_in_jupyter`` for IPython imported but ``get_ipython()`` returns None."""
    _mock_ipython(None)
    assert not running_in_jupyter()


def test_ipython_imported_but_not_in_jupyter():
    """Test ``running_in_jupyter`` for IPython imported but not in Jupyter."""
    _mock_ipython(MockIPython(None))
    assert not running_in_jupyter()


def test_ipython_imported_and_in_jupyter():
    """Test ``running_in_jupyter`` for IPython imported and in Jupyter."""
    _mock_ipython(MockIPython("non-empty kernel"))
    assert running_in_jupyter()


def test_get_jobs_no_results(capfd):
    """Test ``get_jobs`` stdout for results == 0.
    When no results are found, a single line is printed.
    """
    _mock_ipython(MockIPython(None))
    provider = QbraidProvider(client=MockQbraidClient())
    provider.display_jobs(device_id="non-existent-device")
    out, err = capfd.readouterr()
    assert out == "No jobs found matching given criteria\n"
    assert len(err) == 0


def test_get_aws_jobs_by_tag(capfd):
    """Test ``get_jobs`` for aws tagged jobs."""
    _mock_ipython(MockIPython(None))
    qbraid_provider = QbraidProvider(client=MockQbraidClient())
    qbraid_provider.display_jobs(tags={"test": "123"}, provider="aws", max_results=1)
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert MOCK_JOB_DATA[0]["qbraidJobId"] in out
    assert len(err) == 0


def test_get_ibm_jobs_by_tag(capfd):
    """Test ``get_jobs`` for ibm tagged jobs."""
    _mock_ipython(MockIPython(None))
    qbraid_provider = QbraidProvider(client=MockQbraidClient())
    qbraid_provider.display_jobs(tags={"test": "*"}, provider="ibm", max_results=1)
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert MOCK_JOB_DATA[1]["qbraidJobId"] in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_qbraid_jobs_by_tag(capfd):
    """Test ``get_jobs`` for ibm tagged jobs."""
    _mock_ipython(MockIPython(None))
    circuit = random_circuit("cirq")
    provider = QbraidProvider()
    device = provider.get_device("qbraid_qir_simulator")
    if not device.status().name == "ONLINE":
        pytest.skip("qBraid QIR simulator not available")
    job = device.run(circuit, shots=1, tags={"test": "456"})
    provider.display_jobs(tags={"test": "456"}, max_results=1)
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert job.id in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_jobs_results(capfd):
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
    _mock_ipython(MockIPython(None))
    num_results = 1  # test value
    lines_expected = 5 + num_results
    provider = QbraidProvider()
    provider.display_jobs(max_results=num_results)
    out, err = capfd.readouterr()
    lines_out = len(out.split("\n"))
    if lines_out == 2:
        pytest.skip("No jobs found")
    assert lines_out == lines_expected
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_display_jobs_in_jupyter(capfd):
    """Test ``_display_jobs_jupyter`` stdout for non-empty job status list."""
    _mock_ipython(MockIPython("non-empty kernel"))
    data = []
    for index, value in enumerate(job_status_list):
        job_id = f"job_{index}"
        timestamp = f"timestamp_{index}"
        status_str = value
        job_tuple = (job_id, timestamp, status_str)
        data.append(job_tuple)
    msg = "test123"
    _job_table_jupyter(data, msg)
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_jobs_in_jupyter(capfd):
    """Test ``get_jobs`` stdout for non-empty kernel.
    When running in Jupyter, the output should be an HTML object."""
    _mock_ipython(MockIPython("non-empty kernel"))
    provider = QbraidProvider()
    provider.display_jobs()
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


def get_ipython():
    """Mock get_ipython function."""
    pass


def _mock_ipython(get_ipython_result):
    """Mock IPython module and get_ipython function."""
    module = sys.modules["test_display"]
    sys.modules["IPython"] = module

    get_ipython = Mock(return_value=get_ipython_result)
    sys.modules["IPython"].__dict__["get_ipython"] = get_ipython


class MockIPython:
    """Mock IPython class for testing"""

    def __init__(self, kernel):
        self.kernel = kernel
