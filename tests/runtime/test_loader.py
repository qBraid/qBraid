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

from qbraid.runtime import (
    PROVIDERS,
    JobLoaderError,
    ProviderLoaderError,
    QbraidProvider,
    get_providers,
    load_job,
    load_provider,
)

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


def test_get_providers():
    """Test getting all available providers."""
    providers = get_providers()
    assert providers == PROVIDERS == ["aws", "azure", "ibm", "ionq", "oqc", "qbraid"]


def test_load_provider(mock_client):
    """Test loading a provider using entrypoints"""
    provider = load_provider("qbraid", client=mock_client)
    assert isinstance(provider, QbraidProvider)


def test_load_provider_error():
    """Test that ProviderLoaderError is raised when loading a provider fails."""
    provider_name = "fake_provider"

    with pytest.raises(
        ProviderLoaderError,
        match=f"Error loading QuantumProvider sub-class for provider '{provider_name}'.",
    ):
        load_provider(provider_name)
