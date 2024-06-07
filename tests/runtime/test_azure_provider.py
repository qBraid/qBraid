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
Unit tests for Azure session, provider, and device classes

"""
import pytest

from qbraid.runtime.azure import AzureQuantumDevice, AzureQuantumProvider, AzureSession


@pytest.mark.skip(reason="Not implemented")
def test_session_get_devices():
    """Test getting data for all Azure Quantum devices."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_session_get_device():
    """Getting data for specific Azure Quantum device."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_session_create_job():
    """Test creating a new job through the Azure Quantum API."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_session_get_job():
    """Teset getting a specific Azure Quantum job."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_session_cancel_job():
    """Test cancelling a specific Azure Quantum job."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_provider_get_devices():
    """Test getting list of all AzureQuantumDevice objects."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_provider_get_device():
    """Test getting a specific AzureQuantumDevice object."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented")
def test_device_status():
    """Test getting status of AzureQuantumDevice."""
    raise NotImplementedError
