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
Module defining mock data and classes for testing the runtime module. 

"""
from typing import Any, Optional
from unittest.mock import MagicMock

from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

DEVICE_DATA_QIR = {
    "numberQubits": 64,
    "pendingJobs": 0,
    "qbraid_id": "qbraid_qir_simulator",
    "name": "QIR sparse simulator",
    "provider": "qBraid",
    "paradigm": "gate-based",
    "type": "SIMULATOR",
    "vendor": "qBraid",
    "runPackage": "pyqir",
    "status": "ONLINE",
    "isAvailable": True,
    "processorType": "State vector",
    "noiseModels": ["ideal"],
    "pricing": {"perTask": 0.005, "perShot": 0, "perMinute": 0.075},
}

DEVICE_DATA_QUERA_QASM = {
    "numberQubits": 30,
    "pendingJobs": 0,
    "qbraid_id": "quera_qasm_simulator",
    "name": "Noisey QASM simulator",
    "provider": "QuEra",
    "paradigm": "gate-based",
    "type": "SIMULATOR",
    "vendor": "qBraid",
    "runPackage": "qasm2",
    "status": "ONLINE",
    "isAvailable": True,
    "processorType": "State vector",
    "noiseModels": ["quera_lqs_backend"],
    "pricing": {"perTask": 0, "perShot": 0, "perMinute": 0},
}

DEVICE_DATA_NEC = {
    "qbraid_id": "nec_vector_annealer",
    "name": "NEC Vector Annealer",
    "provider": "NEC",
    "paradigm": "annealing",
    "type": "SIMULATOR",
    "vendor": "qbraid",
    "status": "ONLINE",
    "isAvailable": True,
    "numberQubits": 0,
    "runPackage": "qubo",
    "pricing": {"perMinute": 0, "perShot": 0.00145, "perTask": 0.3},
}

DEVICE_DATA_AQUILA = {
    "numberQubits": 256,
    "pendingJobs": 9,
    "qbraid_id": "quera_aquila",
    "name": "Aquila",
    "provider": "QuEra",
    "paradigm": "AHS",
    "type": "QPU",
    "vendor": "AWS",
    "runPackage": "braket",
    "status": "OFFLINE",
    "isAvailable": False,
    "architecture": "neutral atom",
    "pricing": {"perTask": 0.3, "perShot": 0.01, "perMinute": 0},
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
    "qbraidJobId": "qbraid_qir_simulator-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "shots": 10,
    "circuitNumQubits": 5,
    "qbraidDeviceId": "qbraid_qir_simulator",
    "vendor": "qbraid",
    "provider": "qbraid",
    "tags": {},
    "experimentType": "gate_model",
    **REDUNDANT_JOB_DATA,
}

JOB_DATA_QUERA_QASM = {
    "qbraidJobId": "quera_qasm_simulator-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "shots": 10,
    "circuitNumQubits": 5,
    "qbraidDeviceId": "quera_qasm_simulator",
    "vendor": "qbraid",
    "provider": "quera",
    "tags": {},
    "experimentType": "gate_model",
    **REDUNDANT_JOB_DATA,
}

JOB_DATA_NEC = {
    "qbraidJobId": "nec_vector_annealer-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "qubo": {("x1", "x1"): 3.0, ("x1", "x2"): 2.0},
    "offset": 0.0,
    "qbraidDeviceId": "nec_vector_annealer",
    "vendor": "qbraid",
    "provider": "nec",
    "tags": {},
    "experimentType": "annealing",
    **REDUNDANT_JOB_DATA,
}

JOB_DATA_AQUILA = {
    "qbraidJobId": "quera_aquila-jovyan-qjob-1234567890",
    "queuePosition": None,
    "queueDepth": None,
    "shots": 100,
    "qbraidDeviceId": "quera_aquila",
    "atomRegister": [
        [0.0, 0.0],
        [0.0, 3.0e-6],
        [0.0, 6.0e-6],
        [3.0e-6, 0.0],
        [3.0e-6, 3.0e-6],
        [3.0e-6, 6.0e-6],
    ],
    "filling": [1, 1, 1, 1, 0, 0],
    "numAtoms": 6,
    "vendor": "aws",
    "provider": "quera",
    "tags": {},
    "experimentType": "ahs",
    **REDUNDANT_JOB_DATA,
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

RESULTS_DATA_QUERA_QASM = {
    "measurementCounts": {"11111": 4, "00000": 6},
    "backend": "cirq-gpu",
    "quera_simulation_result": {
        "flair_visual_version": "0.5.3",
        "counts": {"0": 6, "31": 4},
        "logs": (
            ",atom_id,block_id,action_type,time,duration\n"
            "0,0,TrapSLM,0,0\n"
            "0,0,TrapAOD,0,31.024984394500784\n"
            "0,0,DropAOD,31.024984394500784,0"
        ),
        "atom_animation_state": {
            "block_durations": [],
            "gate_events": [],
            "qpu_fov": {"xmin": -6, "xmax": 218, "ymin": -5, "ymax": 66.5},
            "atoms": [],
            "slm_zone": [],
            "aod_moves": [],
        },
        "noise_model": {"all_qubits": [0, 1, 2, 3, 4], "gate_events": []},
    },
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
    "measurementCounts": {"rrrgeggrrgr": 1, "grggrgrrrrg": 1},
    **REDUNDANT_JOB_DATA,
}


class MockClient:
    """Mock client for testing."""

    @property
    def session(self):
        """Mock session property."""
        session = MagicMock()
        session.api_key = "abc123"
        return session

    @property
    def _user_metadata(self):
        """Mock user metadata property."""
        return {"organization": "qbraid", "role": "guest"}

    def search_devices(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Returns a list of devices matching the given query."""
        if query.get("status") == "Bad status":
            raise QuantumServiceRequestError("No devices found matching given criteria")

        data_qir = DEVICE_DATA_QIR.copy()
        data_quera = DEVICE_DATA_QUERA_QASM.copy()
        data_nec = DEVICE_DATA_NEC.copy()

        if query.get("provider") == "qBraid" or query.get("qbraid_id") == "qbraid_qir_simulator":
            return [data_qir]
        if query.get("provider") == "QuEra" or query.get("qbraid_id") == "quera_qasm_simulator":
            return [data_quera]
        if query.get("provider") == "qBraid" or query.get("qbraid_id") == "nec_vector_annealer":
            return [data_nec]
        if query.get("vendor") == "qBraid":
            return [data_qir, data_quera]
        return []

    # pylint: disable-next=unused-argument
    def get_device(self, qbraid_id: Optional[str] = None, **kwargs):
        """Returns the device with the given ID."""
        if qbraid_id == "qbraid_qir_simulator":
            data = DEVICE_DATA_QIR.copy()
            return data
        if qbraid_id == "quera_qasm_simulator":
            data = DEVICE_DATA_QUERA_QASM.copy()
            return data
        if qbraid_id == "nec_vector_annealer":
            data = DEVICE_DATA_NEC.copy()
            return data
        raise QuantumServiceRequestError("No devices found matching given criteria")

    def create_job(self, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a new quantum job with the given data."""
        device_id = data.get("qbraidDeviceId")
        if device_id == "qbraid_qir_simulator":
            job_data = JOB_DATA_QIR.copy()
            return job_data
        if device_id == "quera_qasm_simulator":
            job_data = JOB_DATA_QUERA_QASM.copy()
            return job_data
        if device_id == "nec_vector_annealer":
            job_data = JOB_DATA_NEC.copy()
            return job_data
        raise QuantumServiceRequestError("Failed to create job")

    @staticmethod
    def _extract_device_id(job_id: str) -> str:
        """Extracts the device ID from the given job ID."""
        try:
            return job_id.split("-")[0]
        except IndexError as err:
            raise ValueError("Invalid job ID format") from err

    def get_job(self, job_id: str) -> dict[str, Any]:
        """Returns the quantum job with the given ID."""
        device_id = self._extract_device_id(job_id)
        if device_id == "qbraid_qir_simulator":
            return JOB_DATA_QIR
        if device_id == "quera_qasm_simulator":
            return JOB_DATA_QUERA_QASM
        if device_id == "nec_vector_annealer":
            return JOB_DATA_NEC
        raise QuantumServiceRequestError("No jobs found matching given criteria")

    # pylint: disable-next=unused-argument
    def get_job_results(self, job_id: str, **kwargs) -> dict[str, Any]:
        """Returns the results of the quantum job with the given ID."""
        device_id = self._extract_device_id(job_id)
        if device_id == "qbraid_qir_simulator":
            results_data = RESULTS_DATA_QIR.copy()
            return results_data
        if device_id == "quera_qasm_simulator":
            results_data = RESULTS_DATA_QUERA_QASM.copy()
            return results_data
        if device_id == "nec_vector_annealer":
            results_data = RESULTS_DATA_NEC.copy()
            return results_data
        raise QuantumServiceRequestError("Failed to retrieve job results")


class MockDevice(QuantumDevice):
    """Mock basic device for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def status(self):
        return DeviceStatus.ONLINE

    def submit(self, *args, **kwargs):
        raise NotImplementedError
