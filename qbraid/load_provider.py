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
import pkg_resources

from .api import QbraidSession
from .exceptions import QbraidError
from .providers import QbraidProvider


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


def device_wrapper(device_id: str):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        device_id: unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.providers.QuantumDevice`: A wrapped quantum device-like object

    Raises:
        :class:`~qbraid.QbraidError`: If ``device_id`` is not a valid device reference.

    """
    session = QbraidSession()
    api_endpoint = "/public/lab/get-devices"
    params_list = [{"qbraid_id": device_id}, {"objArg": device_id}]

    for params in params_list:
        device_lst = session.get(api_endpoint, params=params).json()
        if device_lst:
            break

    if not device_lst:
        raise QbraidError(f"{device_id} is not a valid device ID.")

    device_info = device_lst[0]
    device_id = device_info["objArg"]
    provider = QbraidProvider()
    device_obj = provider.get_device(device_id)

    devices_entrypoints = _get_entrypoints("qbraid.providers")

    vendor = device_info["vendor"].lower()
    ep = f"{vendor}.device"
    device_wrapper_class = devices_entrypoints[ep].load()
    return device_wrapper_class(device_obj)


def job_wrapper(qbraid_job_id: str):
    """Retrieve a job from qBraid API using job ID and return job wrapper object.

    Args:
        qbraid_job_id: qBraid Job ID

    Returns:
        :class:`~qbraid.providers.job.QuantumJob`: A wrapped quantum job-like object

    """
    session = QbraidSession()
    job_lst = session.post(
        "/get-user-jobs", json={"qbraidJobId": qbraid_job_id, "numResults": 1}
    ).json()

    if len(job_lst) == 0:
        raise QbraidError(f"{qbraid_job_id} is not a valid job ID.")

    job_data = job_lst[0]

    try:
        vendor_device_id = job_data["vendorDeviceId"]
        qbraid_device = device_wrapper(vendor_device_id)
    except (KeyError, QbraidError):
        qbraid_device = None

    try:
        status_str = job_data["status"]
    except KeyError:
        status_str = "UNKNOWN"
    vendor_job_id = job_data["vendorJobId"]
    vendor = qbraid_device.vendor.lower()
    devices_entrypoints = _get_entrypoints("qbraid.providers")
    ep = f"{vendor}.job"
    job_wrapper_class = devices_entrypoints[ep].load()
    return job_wrapper_class(
        qbraid_job_id, vendor_job_id=vendor_job_id, device=qbraid_device, status=status_str
    )
