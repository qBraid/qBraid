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

"""Shared Open Quantum runtime fixtures."""
from unittest.mock import patch

import pytest

from qbraid.runtime.openquantum import OpenQuantumProvider

# Mock Data
DEVICE_DATA = {
    "backend_classes": [
        {
            "id": "c1b9a7a3-4b8f-4b3e-8b3e-4b8f4b3e8b3e",
            "name": "OpenQuantum Simulator",
            "description": "A simulator.",
            "type": "SIMULATOR",
            "provider_id": "p1",
            "short_code": "oq-sim",
            "constraint_data": {"max_qubits": 32, "min_qubits": 1},
        },
        {
            "id": "d2c... ",
            "name": "OpenQuantum QPU",
            "description": "A QPU.",
            "type": "QPU",
            "provider_id": "p1",
            "short_code": "oq-qpu-1",
            "constraint_data": {"max_qubits": 25, "min_qubits": 1},
        },
    ],
    "pagination": {"next_cursor": None},
}

ORG_DATA = {"organizations": [{"id": "org_abc123", "name": "Test Org"}]}

UPLOAD_RESPONSE = {"id": "upload_id_123", "url": "https://presigned.url/for/upload"}

PREPARE_RESPONSE = {"id": "prep_id_456"}

PREPARATION_RESULT_COMPLETED = {
    "status": "Completed",
    "quote": [
        {
            "price": 10,
            "execution_plan_id": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
            "name": "Standard Plan",
            "queue_priorities": [
                {
                    "price_increase": 0,
                    "queue_priority_id": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
                    "name": "Standard Queue",
                },
                {
                    "price_increase": 5,
                    "queue_priority_id": "4ea2b9de-2d20-46d4-b1b5-0b71537a584f",
                    "name": "Fast Queue",
                },
            ],
        }
    ],
}

CREATE_JOB_RESPONSE = {"id": "job_xyz789", "status": "CREATED"}

GET_JOB_RESPONSE_COMPLETED = {
    "id": "job_xyz789",
    "status": "Completed",
    "backend_class_id": "oq-sim",
    "execution_plan_id": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
    "queue_priority_id": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
    "output_data_url": "https://presigned.url/for/output",
    "message": "Job completed successfully",
}

GET_JOB_RESPONSE_FAILED = {
    "id": "job_xyz789",
    "status": "Failed",
    "backend_class_id": "oq-sim",
    "output_data_url": None,
    "message": "Job failed due to an error",
}

JOB_OUTPUT_RESPONSE = {"00": 50, "11": 50}


@pytest.fixture(autouse=True)
def _clear_openquantum_env(monkeypatch, request):
    """Keep organization lookup off this machine's environment."""
    if request.node.get_closest_marker("remote"):
        return
    monkeypatch.delenv("OPENQUANTUM_ORGANIZATION_ID", raising=False)


@pytest.fixture
def mock_session():
    """Fixture for a mocked OpenQuantumSession."""
    with patch("qbraid.runtime.openquantum.provider.OpenQuantumSession") as mock_session_cls:
        session = mock_session_cls.return_value
        session.get_devices.return_value = DEVICE_DATA["backend_classes"]

        # Mock get_backend_class_details to return constraint data
        def mock_get_details(backend_id):
            if backend_id == "c1b9a7a3-4b8f-4b3e-8b3e-4b8f4b3e8b3e":
                return {"constraint_data": {"max_qubits": 32, "min_qubits": 1}}
            if backend_id == "d2c... ":
                return {"constraint_data": {"max_qubits": 25, "min_qubits": 1}}
            return {}

        session.get_backend_class_details.side_effect = mock_get_details
        session.get_user_organizations.return_value = ORG_DATA["organizations"]
        session.upload_input.return_value = UPLOAD_RESPONSE["id"]
        session.prepare_job.return_value = PREPARE_RESPONSE
        session.wait_for_preparation.return_value = PREPARATION_RESULT_COMPLETED["quote"]
        session.create_job.return_value = CREATE_JOB_RESPONSE
        session.get_job.return_value = GET_JOB_RESPONSE_COMPLETED
        session.download_job_output.return_value = JOB_OUTPUT_RESPONSE
        yield session


@pytest.fixture
def provider(mock_session):
    """Fixture for an OpenQuantumProvider with a mocked session."""
    with patch.object(
        OpenQuantumProvider,
        "__init__",
        lambda s, client_id=None, client_secret=None: setattr(s, "session", mock_session),
    ):
        prov = OpenQuantumProvider()
        yield prov
