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

"""
Shared fixtures for Azure provider and testing circuit.
"""

import os
from typing import Optional

import pytest
from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum._constants import ConnectionConstants, EnvironmentVariables
from qiskit import QuantumCircuit

from qbraid.runtime.azure import AzureQuantumProvider


@pytest.fixture
def credential() -> Optional[ClientSecretCredential]:
    """Fixture for Azure client secret credential."""
    tenant_id = os.getenv(EnvironmentVariables.AZURE_TENANT_ID)
    client_id = os.getenv(EnvironmentVariables.AZURE_CLIENT_ID)
    client_secret = os.getenv(EnvironmentVariables.AZURE_CLIENT_SECRET)
    if client_id and tenant_id and client_secret:
        return ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )
    return None


@pytest.fixture
def resource_id() -> Optional[str]:
    """Fixture for Azure Quantum resource ID."""
    subscription_id = os.getenv(EnvironmentVariables.QUANTUM_SUBSCRIPTION_ID)
    resource_group = os.getenv(EnvironmentVariables.QUANTUM_RESOURCE_GROUP, "AzureQuantum")
    workspace_name = os.getenv(EnvironmentVariables.WORKSPACE_NAME)
    if subscription_id and resource_group and workspace_name:
        return ConnectionConstants.VALID_RESOURCE_ID(
            subscription_id=subscription_id,
            resource_group=resource_group,
            workspace_name=workspace_name,
        )
    return None


@pytest.fixture
def workspace(
    credential: Optional[ClientSecretCredential], resource_id: Optional[str]
) -> Workspace:
    """Fixture for Azure Quantum workspace."""
    location = os.getenv(EnvironmentVariables.QUANTUM_LOCATION, "eastus")
    return Workspace(resource_id=resource_id, location=location, credential=credential)


@pytest.fixture
def provider(workspace: Workspace) -> AzureQuantumProvider:
    """Fixture for AzureQuantumProvider."""
    return AzureQuantumProvider(workspace)


@pytest.fixture
def qiskit_circuit() -> QuantumCircuit:
    """Fixture for a Qiskit quantum circuit."""
    circuit = QuantumCircuit(3, 3)
    circuit.name = "main"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])

    return circuit
