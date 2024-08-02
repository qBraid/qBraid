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
Module defining all :mod:`~qbraid.runtime` enumerated types.

"""
from enum import Enum


class DeviceActionType(Enum):
    """
    Enumeration for the quantum device action types
    supported natively by qBraid.

    Attributes:
        OPENQASM (str): Actions compatible with OpenQASM (gate-model).
        AHS (str): Actions using analog Hamiltonian simulation.
        ANNEALING (str): Actions using quantum annealing.
    """

    OPENQASM = "qbraid.programs.circuits"
    AHS = "qbraid.programs.ahs"


class DeviceStatus(Enum):
    """Enumeration for representing various operational statuses of devices.

    Attributes:
        ONLINE (str): Device is online and accepting jobs.
        UNAVAILABLE (str): Device is online but not accepting jobs.
        OFFLINE (str): Device is offline.
        RETIRED (str): Device has been retired and is no longer operational.
    """

    ONLINE = "online"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"
    RETIRED = "retired"


class JobStatus(Enum):
    """Class for the status of processes (i.e. jobs / quantum tasks) resulting from any
    :meth:`~qbraid.runtime.QuantumDevice.run` method.

    Attributes:
        INITIALIZING (str): job is being initialized
        QUEUED (str): job is queued
        VALIDATING (str): job is being validated
        RUNNING (str): job is actively running
        CANCELLING (str): job is being cancelled
        CANCELLED (str): job has been cancelled
        COMPLETED (str): job has successfully run
        FAILED (str): job failed / incurred error
        UNKNOWN (str): job status is unknown/undetermined

    """

    INITIALIZING = "job is being initialized"
    QUEUED = "job is queued"
    VALIDATING = "job is being validated"
    RUNNING = "job is actively running"
    CANCELLING = "job is being cancelled"
    CANCELLED = "job has been cancelled"
    COMPLETED = "job has successfully run"
    FAILED = "job failed / incurred error"
    UNKNOWN = "job status is unknown/undetermined"


JOB_STATUS_FINAL = (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED)
