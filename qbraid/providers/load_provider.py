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
Module containing top-level qbraid wrapper functionality. Each of these
functions utilize entrypoints via ``pkg_resources``.

"""
import warnings

from .job import QuantumJob
from .provider import QbraidProvider


def device_wrapper(device_id: str):
    """(DEPRECATED) Apply qbraid device wrapper to device from a supported device provider.

    Args:
        device_id: unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.providers.QuantumDevice`: A wrapped quantum device-like object
    """
    warnings.warn(
        "qbraid.device_wrapper() is deprecated. Please use \
        qbraid.providers.QbraidProvider.get_device() instead.",
        PendingDeprecationWarning,
    )
    provider = QbraidProvider()
    return provider.get_device(device_id)


def job_wrapper(qbraid_job_id: str):
    """(DEPRECATED) Retrieve a job from qBraid API using job ID and return job wrapper object.

    Args:
        qbraid_job_id: qBraid Job ID

    Returns:
        :class:`~qbraid.providers.job.QuantumJob`: A wrapped quantum job-like object

    """
    warnings.warn(
        "qbraid.job_wrapper() is deprecated. Please use \
        qbraid.providers.QuantumJob.retrieve() instead.",
        PendingDeprecationWarning,
    )
    return QuantumJob.retrieve(qbraid_job_id)
