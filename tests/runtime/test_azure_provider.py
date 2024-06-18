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

provider = AzureQuantumProvider(client_id=client_id, client_secret=client_secret, tenant_id=tenant_id,
                                location_name=location_name, subscription_id=subscription_id, resource_group_name=resource_group,
                                workspace_name=workspace_name, storage_account=storage_account, connection_string=connection_string)

session = provider.session

@pytest.fixture
def test_session_get_devices():
    """Test getting data for all Azure Quantum devices."""
    check_devices = ['microsoft.estimator', 'quantinuum.qpu.h1-1', 'quantinuum.sim.h1-1sc', 'quantinuum.sim.h1-1e', 'rigetti.sim.qvm', 'rigetti.qpu.ankaa-2']
    all_devices = []

    devices = session.get_devices()
    for device, data in devices.items():
        all_devices.append(device)

    assert all_devices == check_devices


def test_session_get_device():
    """Getting data for specific Azure Quantum device."""
    check_parameters = ['status', 'isAvailable', 'nextAvailable', 'availablilityCD', 'averageQueueTime']
    device_parameters = []

    device = session.get_device("microsoft.estimator")
    for parameter, status in device.items():
        device_parameters.append(parameter)

    assert device_parameters == check_parameters

def test_session_create_job():
    """Test creating a new job through the Azure Quantum API."""

    check_parameters = ['containerUri', 'inputDataUri', 'inputDataFormat', 
                        'inputParams', 'metadata', 'sessionId', 'status', 
                        'jobType', 'outputDataFormat', 'outputDataUri', 
                        'beginExecutionTime', 'cancellationTime', 'quantumComputingData', 
                        'errorData', 'isCancelling', 'tags', 'name', 
                        'id', 'providerId', 'target', 'creationTime', 
                        'endExecutionTime', 'costEstimate', 'itemType']
    
    job_parameters = []

    job = session.create_job("job-data-test-cases", "quantinuum", "Emulator", 2)

    for parameter, status in job.items():
            job_parameters.append(parameter)

    assert job_parameters == check_parameters

def test_session_get_job():
    """Teset getting a specific Azure Quantum job."""
    check_parameters = ['containerUri', 'inputDataUri', 'inputDataFormat', 
                        'inputParams', 'metadata', 'sessionId', 'status', 
                        'jobType', 'outputDataFormat', 'outputDataUri', 
                        'beginExecutionTime', 'cancellationTime', 'quantumComputingData', 
                        'errorData', 'isCancelling', 'tags', 'name', 
                        'id', 'providerId', 'target', 'creationTime', 
                        'endExecutionTime', 'costEstimate', 'itemType']
    
    job_parameters = []

    session.create_job("job-data-test-cases", "quantinuum", "Emulator", 2)

    for key, value in session.jobs.items():
        job_id = key
        break

    get_job = session.get_job(job_id)

    for parameter, status in get_job.items():
            job_parameters.append(parameter)

    assert job_parameters == check_parameters

def test_session_cancel_job():
    """Test cancelling a specific Azure Quantum job."""
    session.create_job("job-data-test-cases", "quantinuum", "Emulator", 2)

    for key, value in session.jobs.items():
        job_id = key
        break

    session.cancel_job(job_id)
    metadata = session.get_job(job_id)

    assert metadata["isCancelling"] == True
    
@pytest.fixture
def test_provider_get_devices():
    """Test getting list of all AzureQuantumDevice objects."""
    devices = provider.get_devices()
    assert len(devices) >= 1


def test_provider_get_device():
    """Test getting a specific AzureQuantumDevice object."""
    check_devices = ['id', 'status', 'isAvailable', 'nextAvailable', 'availablilityCD', 'averageQueueTime']
    verify_devices = []

    devices = provider.get_device("microsoft.estimator")

    for parameter, status in devices.items():
        verify_devices.append(parameter)

    assert check_devices == verify_devices
    
def test_device_status():
    """Test getting status of AzureQuantumDevice."""
    devices = provider.get_device("microsoft.estimator")
    assert "status" in devices
    
