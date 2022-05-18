"""Module for interacting with qbraid job API"""

import os
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from .session import QbraidSession

if TYPE_CHECKING:
    import qbraid


def init_job(
    vendor_job_id: str,
    device: 'qbraid.devices.DeviceLikeWrapper',
    circuit: 'qbraid.transpiler.QuantumProgramWrapper',
    shots: int,
) -> str:
    """Initialize data dictionary for new qbraid job and
    create associated MongoDB job document.

    Args:
        vendor_job_id: Job ID provided by device vendor
        device: Wrapped quantum device
        circuit: Wrapped quantum circuit
        shots: Number of shots

    Returns:
        The qbraid job ID associated with this job

    """
    from qbraid.devices.enums import JobStatus  # pylint: disable=import-outside-toplevel

    session = QbraidSession()

    status = JobStatus.INITIALIZING

    init_data = {
        "qbraidJobId": "",
        "vendorJobId": vendor_job_id,
        "qbraidDeviceId": device.id,
        "circuitNumQubits": circuit.num_qubits,
        "circuitDepth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": status.raw()
    }
    init_data["email"] = os.getenv("JUPYTERHUB_USER")
    return session.post("/init-job", data=init_data).json()


def get_job_data(qbraid_job_id: str, status: 'Optional[qbraid.devices.JobStatus]') -> dict:
    """Update a new MongoDB job document.

    Args:
        qbraid_job_id: The qbraid job ID associated with the job
        status: Job status update

    Returns:
        The metadata associated with this job

    """
    session = QbraidSession()
    body = {"qbraidJobId": qbraid_job_id}
    if status:
        body["status"] = status.raw()
    metadata = session.put("/update-job", data=body).json()[0]
    metadata.pop("_id", None)
    metadata.pop("user", None)
    return metadata
