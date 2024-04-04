# Copyright (C) 2023 qBraid
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
from unittest.mock import Mock

import pytest

from qbraid import __version__
from qbraid._display import running_in_jupyter, update_progress_bar
from qbraid.get_devices import get_devices
from qbraid.get_jobs import _display_jupyter, get_jobs
from qbraid.interface.random import random_circuit
from qbraid.programs.exceptions import PackageValueError
from qbraid.providers import QbraidProvider

# pylint: disable=missing-function-docstring,redefined-outer-name

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS") is None
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid/AWS/IBM storage)"


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


def test_update_progress_bar_done(capfd):
    """Test ``update_progress_bar`` for status 'Done'."""
    progress_val = 1
    expected_out = "\rProgress: [....................] 100% Done\r\n"
    update_progress_bar(progress_val)
    out, err = capfd.readouterr()
    assert out == expected_out
    assert len(err) == 0


def test_update_progress_bar_halted(capfd):
    """Test ``update_progress_bar`` for status 'Halted'."""
    progress_val = -1
    expected_out = "\rProgress: [                    ] 0% Halted\r\n"
    update_progress_bar(progress_val)
    out, err = capfd.readouterr()
    assert out == expected_out
    assert len(err) == 0


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


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_jobs_no_results(capfd):
    """Test ``get_jobs`` stdout for results == 0.
    When no results are found, a single line is printed.
    """
    _mock_ipython(MockIPython(None))
    get_jobs(filters={"circuitNumQubits": -1})
    out, err = capfd.readouterr()
    assert out == "No jobs found matching given criteria\n"
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_aws_jobs_by_tag(capfd):
    """Test ``get_jobs`` for aws tagged jobs."""
    _mock_ipython(MockIPython(None))
    circuit = random_circuit("braket")
    provider = QbraidProvider()
    device = provider.get_device("aws_dm_sim")
    job = device.run(circuit, shots=10, tags={"test": "123"})
    get_jobs(filters={"tags": {"test": "123"}, "numResults": 1})
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert job.id in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_ibm_jobs_by_tag(capfd):
    """Test ``get_jobs`` for ibm tagged jobs."""
    _mock_ipython(MockIPython(None))
    circuit = random_circuit("qiskit")
    provider = QbraidProvider()
    device = provider.get_device("ibm_q_qasm_simulator")
    job = device.run(circuit, shots=10, tags=["test"])
    get_jobs(filters={"tags": {"test": "*"}, "numResults": 1})
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
    num_results = 3  # test value
    lines_expected = 5 + num_results
    get_jobs(filters={"numResults": num_results})
    out, err = capfd.readouterr()
    lines_out = len(out.split("\n"))
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
    _display_jupyter(data, msg)
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_jobs_in_jupyter(capfd):
    """Test ``get_jobs`` stdout for non-empty kernel.
    When running in Jupyter, the output should be an HTML object."""
    _mock_ipython(MockIPython("non-empty kernel"))
    get_jobs()
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


def test_get_devices_no_results(capfd):
    """Test ``get_devices`` stdout for results == 0, no refresh.
    When no results are found, a single line is printed.
    """
    _mock_ipython(MockIPython(None))
    get_devices(filters={"numberQubits": -1})
    out, err = capfd.readouterr()
    assert out == "No results matching given criteria\n"
    assert len(err) == 0


def test_get_devices_results(capfd):
    """Test ``get_devices`` stdout for results > 0, no refresh.
    When results returned, output format is as follows:
    (1) Message
    (2) Section titles
    (3) Underline titles
    (4+x) ``x`` lines of results
    (5+x) Empty line

    So, for a query returning ``x`` results, we expect ``5+x`` total lines from stdout.
    """
    _mock_ipython(MockIPython(None))
    get_devices(filters={"qbraid_id": "ibm_q_qasm_simulator"})
    num_results = 1  # searching by device id will return one result
    lines_expected = 5 + num_results
    out, err = capfd.readouterr()
    lines_out = len(out.split("\n"))
    assert lines_out == lines_expected
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_devices_refresh_results(capfd):
    """Test ``get_devices`` stdout for results > 0, with refresh.
    When results returned, output format is as follows:
    (1) Progress bar
    (2) Empty line
    (3) Message
    (4) Empty line
    (5) Section titles
    (6) Underline titles
    (7+x) ``x`` lines of results

    So for a query returning ``x`` results, we expect ``6+x`` total lines from stdout.
    """
    _mock_ipython(MockIPython(None))
    get_devices(filters={"qbraid_id": "ibm_q_qasm_simulator"}, refresh=True)
    num_results = 1  # searching by device id will return one result
    lines_expected = 7 + num_results
    out, err = capfd.readouterr()
    lines_out = len(out.split("\n"))
    assert lines_out == lines_expected
    assert len(err) == 0


def test_get_devices_in_jupyter(capfd):
    """Test ``get_devices`` stdout for non-empty kernel.
    When running in Jupyter, the output should be an HTML object."""
    _mock_ipython(MockIPython("non-empty kernel"))
    get_devices()
    out, err = capfd.readouterr()
    assert "IPython.core.display.HTML object" in out
    assert len(err) == 0


def get_ipython():
    """Mock get_ipython function."""
    pass


def _mock_ipython(get_ipython_result):
    """Mock IPython module and get_ipython function."""
    module = sys.modules["test_top_level"]
    sys.modules["IPython"] = module

    get_ipython = Mock(return_value=get_ipython_result)
    sys.modules["IPython"].__dict__["get_ipython"] = get_ipython


class MockIPython:
    """Mock IPython class for testing"""

    def __init__(self, kernel):
        self.kernel = kernel
