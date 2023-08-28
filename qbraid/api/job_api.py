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
import sys
from typing import Optional

from .session import QbraidSession

SLUG = "qbraid_sdk_9j9sjy"  # qBraid Lab environment ID.
ENVS_PATH = os.getenv("QBRAID_USR_ENVS") or os.path.join(
    os.path.expanduser("~"), ".qbraid", "environments"
)
SLUG_PATH = os.path.join(ENVS_PATH, SLUG)


def _running_in_lab() -> bool:
    """Checks if you are running qBraid-SDK in qBraid Lab environment.

    See https://docs.qbraid.com/en/latest/lab/environments.html
    """
    python_exe = os.path.join(SLUG_PATH, "pyenv", "bin", "python")
    return sys.executable == python_exe


def _qbraid_jobs_enabled(vendor: Optional[str] = None) -> bool:
    """Returns True if running qBraid Lab and qBraid Quantum Jobs
    proxy is enabled. Otherwise, returns False.

    See https://docs.qbraid.com/en/latest/lab/quantum_jobs.html
    """
    # currently quantum jobs only supported for AWS
    if vendor and vendor != "aws":
        return False

    proxy_file = os.path.join(SLUG_PATH, "qbraid", "proxy")
    if os.path.isfile(proxy_file):
        with open(proxy_file) as f:  # pylint: disable=unspecified-encoding
            firstline = f.readline().rstrip()
            return "active = true" in firstline  # check if proxy is active or not

    return False


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
