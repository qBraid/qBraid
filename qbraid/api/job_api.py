"""Module for interacting with qbraid job API"""

import os
from datetime import datetime

from qbraid import api
from qbraid.devices.enums import JobStatus


def mongo_init_job(init_data):
    """Create a new MongoDB job document.

    Returns:
        str: the qbraid_job_id associated with this job

    """
    init_data["user"] = os.getenv("JUPYTERHUB_USER")
    qbraid_job_id = api.post("/init-job", data=init_data)
    return qbraid_job_id


def mongo_get_job(qbraid_job_id, update=None):
    """Update a new MongoDB job document.

    Returns:
        dict: the metadata associated with this job

    """
    data = {} if not update else update
    body = {"qbraid_job_id": qbraid_job_id, "update": data}
    metadata = api.put("/update-job", data=body)
    del metadata["_id"]
    return metadata


def init_job(vendor_job_id, device, circuit, shots):
    """Initialize data dictionary for new qbraid job and pass to mongo init function"""
    data = {
        "qbraid_job_id": "",
        "vendor_job_id": vendor_job_id,
        "qbraid_device_id": device.id,
        "circuit_num_qubits": circuit.num_qubits,
        "circuit_depth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": JobStatus.INITIALIZING,
    }
    return mongo_init_job(data)
