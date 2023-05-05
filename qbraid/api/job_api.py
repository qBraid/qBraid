# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for interacting with the qBraid Jobs API.

"""
import os
from datetime import datetime
from typing import TYPE_CHECKING

from .session import QbraidSession

if TYPE_CHECKING:
    import qbraid


def _qbraid_jobs_enabled():
    """Returns True if running qBraid Lab and qBraid Quantum Jobs
    proxy is enabled. Otherwise, returns False."""
    qbraid_envs_path = os.path.join(os.path.expanduser("~"), ".qbraid", "environments")
    slug_dir_proxy_file = os.path.join(qbraid_envs_path, "qbraid_sdk_9j9sjy", "qbraid", "proxy")

    # Location of proxy file for SDK environment in qBraid Lab.
    if os.path.isfile(slug_dir_proxy_file):
        with open(slug_dir_proxy_file) as f:  # pylint: disable=unspecified-encoding
            firstline = f.readline().rstrip()
            if firstline == "active = true":  # check if proxy is active or not
                return True
    return False


def init_job(
    vendor_job_id: str,
    device: "qbraid.devices.DeviceLikeWrapper",
    circuit: "qbraid.transpiler.QuantumProgramWrapper",
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
    session = QbraidSession()

    # One of the features of qBraid Quantum Jobs is the ability to send
    # jobs without any credentials using the qBraid Lab platform. In short,
    # the qBraid CLI allows you to enable/disable API proxies for environments
    # that use IBMQ and/or Amazon Braket (Botocore). A ``qbraid`` directory
    # exists for each such environment that contains information about how to
    # toggle the proxies, along with their status. If the qBraid Quantum Jobs
    # proxy is enabled, a MongoDB document has already been created for this job. So,
    # instead of creating a new job document, we instead query the user jobs
    # for the ``vendorJobId`` (for Amazon Braket this is the QuantumTask arn),
    # and return the correspondong ``qbraidJobId``.
    if _qbraid_jobs_enabled():
        job = session.post("/get-user-jobs", json={"vendorJobId": vendor_job_id}).json()[0]
        return job["qbraidJobId"]

    # Create a new MongoDB document for the user job.  The qBraid API creates
    # a unique Job ID, which is collected in the response. We use dummy variables
    # for each of the status fields, which will be updated via the ``get_job_data``
    # function upon instantiation of the ``JobLikeWrapper`` object.
    init_data = {
        "qbraidJobId": "",
        "vendorJobId": vendor_job_id,
        "qbraidDeviceId": device.id,
        "vendorDeviceId": device.vendor_device_id,
        "circuitNumQubits": circuit.num_qubits,
        "circuitDepth": circuit.depth,
        "shots": shots,
        "createdAt": datetime.utcnow(),
        "status": "UNKNOWN",  # this will be set after we get back the job ID and check status
        "qbraidStatus": "INITIALIZING",
    }
    init_data["email"] = os.getenv("JUPYTERHUB_USER")  # this env variable exists in Lab by default.
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
    # Two status variables so we can track both qBraid and vendor status.
    if update is not None and "status" in update and "qbraidStatus" in update:
        body["status"] = update["status"]
        body["qbraidStatus"] = update["qbraidStatus"]
    metadata = session.put("/update-job", data=body).json()[0]
    metadata.pop("_id", None)
    metadata.pop("user", None)
    return metadata
