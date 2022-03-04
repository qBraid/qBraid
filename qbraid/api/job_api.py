"""Module for interacting with qbraid job API"""

import os
from datetime import datetime

from qbraid.devices.enums import JobStatus

from .session import QbraidSession

session = QbraidSession()


def mongo_init_job(init_data):
    """Create a new MongoDB job document.

    Returns:
        str: the qbraid_job_id associated with this job

    """
    init_data["email"] = os.getenv("JUPYTERHUB_USER")
    qbraid_job_id = session.post("/init-job", data=init_data).json()
    return qbraid_job_id


def mongo_get_job(qbraid_job_id, update=None):
    """Update a new MongoDB job document.

    Returns:
        dict: the metadata associated with this job

    """
    data = {} if not update else update
    body = {"qbraidJobId": qbraid_job_id, "update": data}
    metadata = session.put("/update-job", data=body).json()
    del metadata["_id"]
    return metadata


def init_job(vendor_job_id, device, circuit, shots):
    """Initialize data dictionary for new qbraid job and pass to mongo init function"""
    data = {
        "qbraidJobId": "",
        "vendorJobId": vendor_job_id,
        "qbraidDeviceId": device.id,
        "circuitNumQubits": circuit.num_qubits,
        "circuitDepth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": JobStatus.INITIALIZING,
    }
    return mongo_init_job(data)
