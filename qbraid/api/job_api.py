"""Module for interacting with qbraid job API"""

import os
from datetime import datetime

from .session import QbraidSession


def init_job(vendor_job_id, device, circuit, shots):
    """Initialize data dictionary for new qbraid job and
    create associated MongoDB job document.

    Returns:
        str: the qbraid_job_id associated with this job

    """
    from qbraid.devices.enums import JobStatus  # pylint: disable=import-outside-toplevel

    session = QbraidSession()

    init_data = {
        "qbraidJobId": "",
        "vendorJobId": vendor_job_id,
        "qbraidDeviceId": device.id,
        "circuitNumQubits": circuit.num_qubits,
        "circuitDepth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": JobStatus.INITIALIZING,
    }
    init_data["email"] = os.getenv("JUPYTERHUB_USER")
    return session.post("/init-job", data=init_data).json()


def get_job_data(qbraid_job_id, status=None):
    """Update a new MongoDB job document.

    Returns:
        dict: the metadata associated with this job

    """
    session = QbraidSession()
    body = {"qbraidJobId": qbraid_job_id}
    if status:
        body["status"] = status
    metadata = session.put("/update-job", data=body).json()[0]
    metadata.pop("_id", None)
    metadata.pop("user", None)
    return metadata
