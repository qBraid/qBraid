# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for loading jobs using entrypoints

"""

import pytest

from qbraid.runtime import JobLoaderError, load_job

from ._resources import JOB_DATA_QIR


@pytest.fixture
def job_id():
    """Mock job data for testing"""
    return JOB_DATA_QIR["qbraidJobId"]


def test_load_job(mock_client, job_id):
    """Test loading a job using entrypoints"""
    job = load_job(job_id, "qbraid", client=mock_client)
    assert job.id == job_id


def test_load_job_error(job_id):
    """Test that JobLoaderError is raised when loading a job fails."""
    provider = "fake_provider"

    with pytest.raises(
        JobLoaderError,
        match=f"Error loading QuantumJob sub-class for provider '{provider}'.",
    ):
        load_job(job_id, provider)
