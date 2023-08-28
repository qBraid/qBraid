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
Module to map qbraid status to equivalent status of each
supported front-end.

"""
from .enums import JobStatus

AwsQuantumTask = {
    "CREATED": JobStatus.INITIALIZING,
    "QUEUED": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "CANCELLING": JobStatus.CANCELLING,
    "CANCELLED": JobStatus.CANCELLED,
    "COMPLETED": JobStatus.COMPLETED,
    "FAILED": JobStatus.FAILED,
}

IBMJob = {
    "JobStatus.INITIALIZING": JobStatus.INITIALIZING,
    "JobStatus.QUEUED": JobStatus.QUEUED,
    "JobStatus.VALIDATING": JobStatus.VALIDATING,
    "JobStatus.RUNNING": JobStatus.RUNNING,
    "JobStatus.CANCELLED": JobStatus.CANCELLED,
    "JobStatus.DONE": JobStatus.COMPLETED,
    "JobStatus.ERROR": JobStatus.FAILED,
}

STATUS_MAP = {"AWS": AwsQuantumTask, "IBM": IBMJob}
