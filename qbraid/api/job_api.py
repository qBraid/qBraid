"""Module for interacting with qbraid job API"""

import os
from datetime import datetime
from typing import TYPE_CHECKING  # pylint: disable=unused-import

from .session import QbraidSession

if TYPE_CHECKING:
    import qbraid


def _braket_proxy():
    home = os.getenv("HOME")
    proxy = f"{home}/.qbraid/environments/qbraid_sdk_9j9sjy/qbraid/botocore/proxy"
    if os.path.isfile(proxy):
        with open(proxy) as f:
            firstline = f.readline().rstrip()
            if firstline == 'active = true':
                return True
    return False


def init_job(
    vendor_job_id: str,
    device: "qbraid.devices.DeviceLikeWrapper",
    circuit: "qbraid.transpiler.QuantumProgramWrapper",
    shots: int
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
    session = QbraidSession()

    if device.vendor == 'AWS' and _braket_proxy():
        job = session.post("/get-user-jobs", json={"vendorJobId": vendor_job_id}).json()[0]
        return job["qbraidJobId"]

    init_data = {
        "qbraidJobId": "",
        "vendorJobId": vendor_job_id,
        "qbraidDeviceId": device.id,
        "circuitNumQubits": circuit.num_qubits,
        "circuitDepth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": "TBD",
        "qbraidStatus": "INITIALIZING"
    }
    init_data["email"] = os.getenv("JUPYTERHUB_USER")
    return session.post("/init-job", data=init_data).json()


def get_job_data(qbraid_job_id: str, update: dict = None) -> dict:
    """Update a new MongoDB job document.

    Args:
        qbraid_job_id: The qbraid job ID associated with the job
        status: Job status update

    Returns:
        The metadata associated with this job

    """
    session = QbraidSession()
    body = {"qbraidJobId": qbraid_job_id}
    if update is not None and "status" in update and "qbraidStatus" in update:
        body["status"] = update["status"]
        body["qbraidStatus"] = update["qbraidStatus"]
    metadata = session.put("/update-job", data=body).json()[0]
    metadata.pop("_id", None)
    metadata.pop("user", None)
    return metadata
