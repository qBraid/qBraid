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
from qbraid_core.services.quantum import QuantumClient

from qbraid import __version__
from qbraid.display import _display_jupyter, _running_in_jupyter, display_jobs
from qbraid.interface.random import random_circuit
from qbraid.programs.exceptions import PackageValueError
from qbraid.runtime.aws import BraketProvider
from qbraid.runtime.ibm import QiskitRuntimeProvider

# pylint: disable=missing-function-docstring,redefined-outer-name

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid/AWS/IBM storage)"

jobs_state_libs = QuantumClient.qbraid_jobs_state().get("libs", {})
braket_enabled = jobs_state_libs.get("braket", {}).get("enabled", False)
qiskit_enabled = jobs_state_libs.get("qiskit", {}).get("enabled", False)


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
    assert not _running_in_jupyter()


def test_ipython_imported_but_ipython_none():
    """Test ``running_in_jupyter`` for IPython imported but ``get_ipython()`` returns None."""
    _mock_ipython(None)
    assert not _running_in_jupyter()


def test_ipython_imported_but_not_in_jupyter():
    """Test ``running_in_jupyter`` for IPython imported but not in Jupyter."""
    _mock_ipython(MockIPython(None))
    assert not _running_in_jupyter()


def test_ipython_imported_and_in_jupyter():
    """Test ``running_in_jupyter`` for IPython imported and in Jupyter."""
    _mock_ipython(MockIPython("non-empty kernel"))
    assert _running_in_jupyter()


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_jobs_no_results(capfd):
    """Test ``get_jobs`` stdout for results == 0.
    When no results are found, a single line is printed.
    """
    _mock_ipython(MockIPython(None))
    display_jobs(filters={"circuitNumQubits": -1})
    out, err = capfd.readouterr()
    assert out == "No jobs found matching given criteria\n"
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests or not braket_enabled, reason=REASON)
def test_get_aws_jobs_by_tag(capfd):
    """Test ``get_jobs`` for aws tagged jobs."""
    _mock_ipython(MockIPython(None))
    circuit = random_circuit("braket")
    provider = BraketProvider()
    device = provider.get_device("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    job = device.run(circuit, shots=10, tags={"test": "123"})
    display_jobs(filters={"tags": {"test": "123"}, "numResults": 1})
    out, err = capfd.readouterr()
    message = out.split("\n")[0]
    assert message == "Displaying 1 most recent job matching query:"
    assert job.id in out
    assert len(err) == 0


@pytest.mark.skipif(skip_remote_tests or not qiskit_enabled, reason=REASON)
def test_get_ibm_jobs_by_tag(capfd):
    """Test ``get_jobs`` for ibm tagged jobs."""
    _mock_ipython(MockIPython(None))
    circuit = random_circuit("qiskit")
    provider = QiskitRuntimeProvider()
    device = provider.get_device("ibm_q_qasm_simulator")
    job = device.run(circuit, shots=10, tags=["test"])
    display_jobs(filters={"tags": {"test": "*"}, "numResults": 1})
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
    display_jobs(filters={"numResults": num_results})
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
    display_jobs()
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
