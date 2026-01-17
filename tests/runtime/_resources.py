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
Module defining mock data and classes for testing the runtime module.

"""
from typing import Any, Optional
from unittest.mock import MagicMock

from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError
from qbraid_core.services.runtime.schemas import (
    JobRequest,
    Program,
    Result,
    RuntimeDevice,
    RuntimeJob,
)

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

DEVICE_DATA_QIR = {
    "success": True,
    "data": {
        "_id": "689fa8990970e91064666bdc",
        "vrn": "qbraid_qir_simulator",
        "runInputTypes": ["pyqir"],
        "numberQubits": 64,
        "noiseModels": [],
        "statusMsg": None,
        "nextAvailable": None,
        "avgQueueTime": None,
        "visibility": "public",
        "verified": "verified",
        "activeVersion": "v4",
        "providerId": "67175f6f22b43201cd51920c",
        "qrn": "qbraid:qbraid:sim:qir-sv",
        "__v": 0,
        "createdAt": "2025-08-15T21:37:29.555Z",
        "modality": None,
        "name": "QIR sparse simulator",
        "paradigm": "gate_model",
        "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
        "status": "ONLINE",
        "updatedAt": "2025-08-15T21:37:29.555Z",
        "vendor": "qbraid",
        "image": None,
        "description": "Sparse state vector simulator using QIR compiler. Free of cost.",
        "deviceType": "SIMULATOR",
        "queueDepth": 0,
        "directAccess": True,
        "pricingModel": "fixed",
        "notes": None,
    },
}

DEVICE_DATA_NEC = {
    "success": True,
    "data": {
        "_id": "689fa8990970e91064666be2",
        "vrn": "nec_vector_annealer",
        "runInputTypes": ["qubo"],
        "numberQubits": None,
        "noiseModels": [],
        "statusMsg": None,
        "nextAvailable": None,
        "avgQueueTime": None,
        "visibility": "public",
        "verified": "verified",
        "activeVersion": "v2",
        "providerId": "67175a6822b43201cd5191b9",
        "qrn": "qbraid:nec:sim:vector-annealer",
        "__v": 0,
        "createdAt": "2025-08-15T21:37:29.556Z",
        "modality": None,
        "name": "NEC Vector Annealer",
        "paradigm": "annealing",
        "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
        "status": "OFFLINE",
        "updatedAt": "2025-08-15T21:37:29.556Z",
        "vendor": "qbraid",
        "image": None,
        "description": (
            "Executes proprietary algorithm for annealing processing on "
            'NEC\'s vector supercomputer "SX-Aurora TSUBASA"'
        ),
        "deviceType": "SIMULATOR",
        "queueDepth": 0,
        "directAccess": True,
        "pricingModel": "fixed",
        "notes": None,
    },
}

DEVICE_DATA_AQUILA = {
    "success": True,
    "data": {
        "_id": "689fa8990970e91064666bd7",
        "vrn": "arn:aws:braket:us-east-1::device/qpu/quera/Aquila",
        "runInputTypes": ["braket_ahs"],
        "numberQubits": 256,
        "noiseModels": [],
        "statusMsg": None,
        "nextAvailable": None,
        "avgQueueTime": None,
        "visibility": "public",
        "verified": "verified",
        "activeVersion": None,
        "providerId": "67175b3822b43201cd5191e9",
        "qrn": "aws:quera:qpu:aquila",
        "__v": 0,
        "createdAt": "2025-08-15T21:37:29.555Z",
        "modality": "neutral atom",
        "name": "Aquila",
        "paradigm": "analog",
        "pricing": {"perTask": 30, "perShot": 1, "perMinute": 0},
        "status": "ONLINE",
        "updatedAt": "2026-01-16T22:00:05.292Z",
        "vendor": "aws",
        "image": None,
        "description": "256 qubit analog neutral atom-based QPU",
        "deviceType": "QPU",
        "queueDepth": 4,
        "directAccess": True,
        "pricingModel": "fixed",
        "notes": None,
    },
}

DEVICE_DATA_EQUAL1 = {
    "success": True,
    "data": {
        "_id": "689fa8990970e91064666be8",
        "vrn": "equal1_simulator",
        "runInputTypes": ["qasm2", "qasm3"],
        "numberQubits": 6,
        "noiseModels": ["ideal", "bell-1"],
        "statusMsg": None,
        "nextAvailable": None,
        "avgQueueTime": None,
        "visibility": "public",
        "verified": "verified",
        "activeVersion": None,
        "providerId": "67175f6f22b43201cd51920d",
        "qrn": "qbraid:equal1:sim:bell-1",
        "__v": 0,
        "createdAt": "2025-08-15T21:37:29.555Z",
        "modality": None,
        "name": "Equal1 Bell-1 Simulator",
        "paradigm": "gate_model",
        "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
        "status": "ONLINE",
        "updatedAt": "2025-08-15T21:37:29.555Z",
        "vendor": "qbraid",
        "image": None,
        "description": "Equal1 Bell-1 noise model simulator",
        "deviceType": "SIMULATOR",
        "queueDepth": 0,
        "directAccess": True,
        "pricingModel": "fixed",
        "notes": None,
    },
}

REDUNDANT_JOB_DATA = {
    "timeStamps": {
        "createdAt": "2024-05-23T01:39:11.288Z",
        "endedAt": "2024-05-23T01:39:11.304Z",
        "executionDuration": 16,
    },
    "status": "COMPLETED",
}

JOB_DATA_QIR = {
    "jobQrn": "qbraid:qbraid:sim:qir-sv-37f5-qjob-1234567890",
    "batchJobQrn": None,
    "vendor": "qbraid",
    "provider": "qbraid",
    "status": "COMPLETED",
    "statusMsg": None,
    "experimentType": "gate_model",
    "queuePosition": None,
    "timeStamps": {
        "createdAt": "2024-05-23T01:39:11.288Z",
        "endedAt": "2024-05-23T01:39:11.304Z",
        "executionDuration": 16,
    },
    "cost": 0,
    "estimatedCost": 0,
    "metadata": {},
    "name": "QIR Job",
    "shots": 10,
    "deviceQrn": "qbraid:qbraid:sim:qir-sv",
    "tags": {},
    "runtimeOptions": {},
}

JOB_DATA_NEC = {
    "jobQrn": "qbraid:nec:sim:vector-annealer-37f5-qjob-1234567890",
    "batchJobQrn": None,
    "vendor": "qbraid",
    "provider": "nec",
    "status": "COMPLETED",
    "statusMsg": None,
    "experimentType": "annealing",
    "queuePosition": None,
    "timeStamps": {
        "createdAt": "2024-05-23T01:39:11.288Z",
        "endedAt": "2024-05-23T01:39:11.304Z",
        "executionDuration": 16,
    },
    "cost": 0,
    "estimatedCost": 0,
    "metadata": {},
    "name": "NEC Annealing Job",
    "shots": None,
    "deviceQrn": "qbraid:nec:sim:vector-annealer",
    "tags": {},
    "runtimeOptions": {},
}

JOB_DATA_AQUILA = {
    "jobQrn": "aws:quera:qpu:aquila-37f5-qjob-696aae286a18e4f726abf2af",
    "batchJobQrn": None,
    "vendor": "aws",
    "provider": "quera",
    "status": "COMPLETED",
    "statusMsg": None,
    "experimentType": "analog",
    "queuePosition": None,
    "timeStamps": {
        "createdAt": "2026-01-16T21:31:24.447Z",
        "endedAt": "2026-01-16T21:33:27.771Z",
        "executionDuration": None,
    },
    "cost": 130,
    "estimatedCost": 130,
    "metadata": {},
    "name": "Analog Job",
    "shots": 100,
    "deviceQrn": "aws:quera:qpu:aquila",
    "tags": {},
    "runtimeOptions": {},
}

RESULTS_DATA_QIR = {
    "measurements": [
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0],
        [1, 1, 1, 1, 1],
    ],
    "measurementCounts": {"11111": 4, "00000": 6},
    "runnerVersion": "0.7.4",
    "runnerSeed": None,
    **REDUNDANT_JOB_DATA,
}

RESULTS_DATA_NEC = {
    "solutions": [
        {
            "spin": {" x1": 0, " x2": 0, "x1": 0},
            "energy": 0,
            "time": 0.006517000030726194,
            "constraint": True,
            "memory_usage": 1.189453125,
        }
    ],
    "solutionCount": 1,
    **REDUNDANT_JOB_DATA,
}

RESULTS_DATA_AQUILA = {
    "measurementCounts": {
        "grggrggr": 1,
        "grgrgerg": 1,
        "rgrgrgrg": 1,
        "grgrgrgr": 3,
        "ggrggrgr": 1,
        "ggrgggrr": 1,
        "rgrggrgg": 1,
        "rggrgreg": 1,
    },
    "measurements": [
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 0, 1, 1, 0, 1, 1, 0],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 0, 1, 1],
            "post_sequence": [1, 0, 1, 0, 1, 0, 0, 1],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [0, 1, 0, 1, 0, 1, 0, 1],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 0, 1, 0, 1, 0, 1, 0],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 0, 1, 0, 1, 0, 1, 0],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 1, 0, 1, 1, 0, 1, 0],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 1, 0, 1, 1, 1, 0, 0],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [0, 1, 0, 1, 1, 0, 1, 1],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 0, 1],
            "post_sequence": [0, 1, 1, 0, 1, 0, 0, 1],
        },
        {
            "success": True,
            "pre_sequence": [1, 1, 1, 1, 1, 1, 1, 1],
            "post_sequence": [1, 0, 1, 0, 1, 0, 1, 0],
        },
    ],
}

JOB_DATA_EQUAL1 = {
    "jobQrn": "qbraid:equal1:sim:bell-1-37f5-qjob-2ht3zyghhxsr8gqbu8yj",
    "batchJobQrn": None,
    "vendor": "qbraid",
    "provider": "equal1",
    "status": "COMPLETED",
    "statusMsg": None,
    "experimentType": "gate_model",
    "queuePosition": None,
    "timeStamps": {
        "createdAt": "2025-08-28T18:44:45.000Z",
        "endedAt": "2025-08-28T18:44:45.000Z",
        "executionDuration": 72,
    },
    "cost": 0.015,
    "estimatedCost": 0.015,
    "metadata": {},
    "name": "Equal1 Job",
    "shots": 10,
    "deviceQrn": "qbraid:equal1:sim:bell-1",
    "tags": {},
    "runtimeOptions": {},
}

RESULTS_DATA_EQUAL1 = {
    "measurementCounts": {"00": 5, "11": 5},
    "compiledOutput": (
        "T1BFTlFBU00gMi4wOwppbmNsdWRlICJxZWxpYjEuaW5jIjsKcXJlZyBxWzJdOwpjcmVnIGNbMl07Cmgg"
        "cVswXTsKY3ggcVswXSxxWzFdOwptZWFzdXJlIHFbMF0gLT4gY1swXTsKbWVhc3VyZSBxWzFdIC0+IGNb"
        "MV07"
    ),
    "irType": "qasm2",
    "noiseModel": "bell-1",
    "simulationPlatform": "CPU",
    "executionOptions": None,
}


class MockClient:
    """Mock client for testing with Runtime API format."""

    DEVICE_MAP = {
        "qbraid:qbraid:sim:qir-sv": DEVICE_DATA_QIR,
        "qbraid:nec:sim:vector-annealer": DEVICE_DATA_NEC,
        "aws:quera:qpu:aquila": DEVICE_DATA_AQUILA,
        "qbraid:equal1:sim:bell-1": DEVICE_DATA_EQUAL1,
    }

    JOB_MAP = {
        "qbraid:qbraid:sim:qir-sv": JOB_DATA_QIR,
        "qbraid:nec:sim:vector-annealer": JOB_DATA_NEC,
        "aws:quera:qpu:aquila": JOB_DATA_AQUILA,
        "qbraid:equal1:sim:bell-1": JOB_DATA_EQUAL1,
    }

    RESULTS_MAP = {
        "qbraid:qbraid:sim:qir-sv": RESULTS_DATA_QIR,
        "qbraid:nec:sim:vector-annealer": RESULTS_DATA_NEC,
        "aws:quera:qpu:aquila": RESULTS_DATA_AQUILA,
        "qbraid:equal1:sim:bell-1": RESULTS_DATA_EQUAL1,
    }

    # Job QRN to device QRN mapping
    JOB_QRN_TO_DEVICE = {
        "aws:quera:qpu:aquila-37f5-qjob-696aae286a18e4f726abf2af": "aws:quera:qpu:aquila",
        "qbraid:qbraid:sim:qir-sv-37f5-qjob-1234567890": "qbraid:qbraid:sim:qir-sv",
        "qbraid:nec:sim:vector-annealer-37f5-qjob-1234567890": "qbraid:nec:sim:vector-annealer",
        "qbraid:equal1:sim:bell-1-37f5-qjob-2ht3zyghhxsr8gqbu8yj": "qbraid:equal1:sim:bell-1",
    }

    @property
    def session(self):
        """Mock session property."""
        session = MagicMock()
        session.api_key = "abc123"
        return session

    @property
    def _user_metadata(self):
        """Mock user metadata property."""
        return {
            "valid": True,
            "userId": "6229769a21fff74352121c46",
            "userName": "jovyan",
            "userEmail": "jovyan@example.com",
            "metadata": {
                "acknowledgedTerms": "accepted",
                "tourUser": "completed",
                "acceptedIntelTerms": "accepted",
                "miningDetected": "not_detected",
            },
            "userRoles": ["organization_admin"],
            "userPermissions": [
                "global|organization|organization|manage",
                "global|organization|members|manage",
                "global|organization|billing|manage",
                "global|organization|device|manage",
                "global|organization|jobs|manage",
                "global|organization|projects|manage",
                "global|organization|users|view",
                "global|organization|users|create",
                "global|organization|users|update",
                "global|organization|users|delete",
                "global|organization|*|*",
                "global|organization|members|view",
                "global|organization|billing|view",
                "global|organization|resources|access",
                "global|organization|projects|view",
                "global|organization|jobs|submit",
                "global|labs|environments|install",
                "global|labs|environments|create",
                "global|organization|self|*",
                "global|*|provider|view",
                "custom|qbraid|organizations|create",
                "custom|qbraid|organizations|delete",
                "global|*|organization|update",
            ],
            "organizationId": "507f1f77bcf86cd799439011",
            "organizationUserId": "68f94f8e0c6d3502fd4c37f5",
        }

    # New Runtime API methods
    def list_devices(self) -> list[RuntimeDevice]:
        """Returns a list of all quantum devices."""
        devices = []
        for device_data in [
            DEVICE_DATA_QIR,
            DEVICE_DATA_NEC,
            DEVICE_DATA_AQUILA,
            DEVICE_DATA_EQUAL1,
        ]:
            devices.append(RuntimeDevice.model_validate(device_data["data"]))
        return devices

    def get_device(self, device_qrn: str) -> RuntimeDevice:
        """Returns the metadata for a specific quantum device."""
        device_data = self.DEVICE_MAP.get(device_qrn)
        if device_data is None:
            # Try to find by QRN in data
            for data in self.DEVICE_MAP.values():
                if data["data"].get("qrn") == device_qrn:
                    device_data = data
                    break

        if device_data is None:
            raise ValueError(f"Device {device_qrn} not found in mock data")

        return RuntimeDevice.model_validate(device_data["data"])

    def create_job(self, request: JobRequest) -> RuntimeJob:
        """Submits a new quantum job."""
        device_qrn = request.deviceQrn
        job_data = self.JOB_MAP.get(device_qrn)

        if job_data is None:
            raise ValueError(f"Job data not found for device {device_qrn}")

        # Return a job response in the new format
        # For annealing jobs, shots may be None, but RuntimeJob requires an int > 0
        # Use shots from request if provided, otherwise from job_data, otherwise default to 100
        shots = (
            request.shots if hasattr(request, "shots") and request.shots else job_data.get("shots")
        )
        if shots is None:
            shots = 100  # Default for jobs that don't specify shots

        job_response = {
            "name": job_data.get("name"),
            "shots": shots,
            "deviceQrn": device_qrn,
            "tags": job_data.get("tags", {}),
            "runtimeOptions": job_data.get("runtimeOptions", {}),
            "jobQrn": job_data.get("jobQrn"),
            "batchJobQrn": job_data.get("batchJobQrn"),
            "vendor": job_data.get("vendor"),
            "provider": job_data.get("provider"),
            "status": "INITIALIZING",
            "statusMsg": None,
            "experimentType": job_data.get("experimentType"),
            "queuePosition": None,
            "timeStamps": None,
            "cost": None,
            "estimatedCost": job_data.get("estimatedCost", 130),
            "metadata": job_data.get("metadata", {}),
        }
        return RuntimeJob.model_validate(job_response)

    def get_job(self, job_qrn: str) -> RuntimeJob:
        """Returns the metadata for a specific quantum job."""
        # Try job QRN mapping first
        device_qrn = self.JOB_QRN_TO_DEVICE.get(job_qrn)
        if device_qrn:
            job_data = self.JOB_MAP.get(device_qrn)
        else:
            # Extract device QRN from job QRN (format: deviceQrn-37f5-qjob-...)
            parts = job_qrn.split("-")
            if len(parts) >= 3 and parts[1] == "37f5" and parts[2] == "qjob":
                device_qrn = parts[0]
                job_data = self.JOB_MAP.get(device_qrn)
            else:
                job_data = None

        if job_data is None:
            raise ValueError(f"Job {job_qrn} not found in mock data")

        # Ensure shots is a valid int (RuntimeJob requires int > 0)
        job_data_copy = job_data.copy()
        if job_data_copy.get("shots") is None:
            job_data_copy["shots"] = 100  # Default for jobs that don't specify shots

        return RuntimeJob.model_validate(job_data_copy)

    def get_job_result(self, job_qrn: str) -> Result:
        """Returns the results for a specific quantum job."""
        # Try job QRN mapping first
        device_qrn = self.JOB_QRN_TO_DEVICE.get(job_qrn)
        if not device_qrn:
            # Extract device QRN from job QRN (format: deviceQrn-37f5-qjob-...)
            parts = job_qrn.split("-")
            if len(parts) >= 3 and parts[1] == "37f5" and parts[2] == "qjob":
                device_qrn = parts[0]

        result_data = self.RESULTS_MAP.get(device_qrn)
        if result_data is None:
            raise ValueError(f"Job result for {job_qrn} not found in mock data")

        # Get job data to extract cost and timestamps
        job_data = self.JOB_MAP.get(device_qrn, {})

        # Wrap result data in new format
        result_response = {
            "status": "COMPLETED",
            "cost": str(job_data.get("cost", 0)),
            "timeStamps": job_data.get(
                "timeStamps",
                {
                    "createdAt": "2024-05-23T01:39:11.288Z",
                    "endedAt": "2024-05-23T01:39:11.304Z",
                    "executionDuration": 16,
                },
            ),
            "resultData": result_data,
        }
        return Result.model_validate(result_response)

    def get_job_program(self, job_qrn: str) -> Program:
        """Returns the program data for a specific quantum job."""
        # Return a mock program for AQUILA
        if "aquila" in job_qrn.lower() or "quera" in job_qrn.lower():
            return Program(format="analog", data={})
        # Return QASM2 for Equal1
        if "equal1" in job_qrn.lower():
            return Program(
                format="qasm2",
                data=(
                    'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];'
                    "\nh q[0];\ncx q[0],q[1];\nmeasure q[0] -> c[0];\nmeasure q[1] -> c[1];"
                ),
            )
        # Default program format
        return Program(format="qasm3", data="OPENQASM 3.0;")

    def cancel_job(self, job_qrn: str) -> None:
        """Cancels a specific quantum job."""
        # Mock implementation - no-op for testing

    # Legacy methods for backward compatibility
    def search_devices(self, query: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """Returns a list of devices matching the given query (legacy method)."""
        all_devices = [data["data"].copy() for data in self.DEVICE_MAP.values()]

        if not query:
            return all_devices

        if "status" in query:
            valid_status_values = {status.name for status in DeviceStatus}
            if query["status"] not in valid_status_values:
                raise QuantumServiceRequestError("No devices found matching given criteria")

        devices = [
            device
            for device in all_devices
            if all(device.get(key) == value for key, value in query.items())
        ]

        return devices

    def _get_data(
        self, identifier: str, data_map: dict[str, dict[str, Any]], error_message: str
    ) -> dict[str, Any]:
        """Helper to retrieve data from a mapping, raising an error if not found."""
        try:
            return data_map[identifier].copy()
        except KeyError as err:
            raise QuantumServiceRequestError(error_message) from err

    @staticmethod
    def _extract_device_id(job_id: str) -> str:
        """Extracts the device ID from the given job ID."""
        try:
            # Handle both old and new formats
            if ":" in job_id:
                # New format: extract from QRN
                parts = job_id.split("-")
                if len(parts) > 0:
                    qrn_part = parts[0]
                    if ":" in qrn_part:
                        return qrn_part.split(":")[-1]
            # Old format
            return job_id.split("-")[0]
        except IndexError as err:
            raise ValueError("Invalid job ID format") from err

    # pylint: disable-next=unused-argument
    def get_job_results(self, job_id: str, **kwargs) -> dict[str, Any]:
        """Returns the results of the quantum job with the given ID (legacy method)."""
        device_id = self._extract_device_id(job_id)
        return self._get_data(
            identifier=device_id,
            data_map=self.RESULTS_MAP,
            error_message="Failed to retrieve job results",
        )


class MockDevice(QuantumDevice):
    """Mock basic device for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def status(self):
        return DeviceStatus.ONLINE

    def submit(self, *args, **kwargs):
        raise NotImplementedError
