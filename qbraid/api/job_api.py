# Copyright 2023 qBraid
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
Module for interacting with the qBraid Jobs API.

"""
import os
from datetime import datetime
from typing import TYPE_CHECKING

from .session import QbraidSession

if TYPE_CHECKING:
    import qbraid


def _braket_proxy():
    """Returns True if running qBraid Lab and the Amazon Braket
    Botocore proxy is enabled. Otherwise, returns False."""
    home = os.getenv("HOME")
    package = "botocore"
    slug = "qbraid_sdk_9j9sjy"
    proxy = f"{home}/.qbraid/environments/{slug}/qbraid/{package}/proxy"

    # Location of Amazon Braket proxy file for SDK environment in qBraid Lab.
    if os.path.isfile(proxy):
        with open(proxy) as f:  # pylint: disable=unspecified-encoding
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
    # toggle the proxies, along with their status. If the Amazon Braket Botocore
    # proxy is enabled, a MongoDB document has already been created for this job. So,
    # instead of creating a new job document, we instead query the user jobs
    # for the ``vendorJobId`` (for Amazon Braket this is the QuantumTask arn),
    # and return the correspondong ``qbraidJobId``.
    if device.vendor == "AWS" and _braket_proxy():
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
