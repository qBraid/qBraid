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

from ._qprogram import QPROGRAM
from .api import QbraidSession
from .exceptions import QbraidError
from .qasm_checks import get_qasm_version


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


def circuit_wrapper(program: QPROGRAM):
    """Apply qbraid quantum program wrapper to a supported quantum program.

    This function is used to create a qBraid :class:`~qbraid.transpiler.QuantumProgramWrapper`
    object, which can then be transpiled to any supported quantum circuit-building package.
    The input quantum circuit object must be an instance of a circuit object derived from a
    supported package.

    .. code-block:: python

        cirq_circuit = cirq.Circuit()
        q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]
        ...

    Please refer to the documentation of the individual qbraid circuit wrapper objects to see
    any additional arguments that might be supported.

    Args:
        circuit (:data:`~qbraid.QPROGRAM`): A supported quantum circuit / program object

    Returns:
        :class:`~qbraid.transpiler.QuantumProgramWrapper`: A wrapped quantum circuit-like object

    Raises:
        :class:`~qbraid.QbraidError`: If the input circuit is not a supported quantum program.

    """
    if isinstance(program, str):
        package = get_qasm_version(program)

    else:
        try:
            package = program.__module__.split(".")[0]
        except AttributeError as err:
            raise QbraidError(
                f"Error applying circuit wrapper to quantum program \
                of type {type(program)}"
            ) from err

    ep = package.lower()

    transpiler_entrypoints = _get_entrypoints("qbraid.transpiler")

    if package in transpiler_entrypoints:
        circuit_wrapper_class = transpiler_entrypoints[ep].load()
        return circuit_wrapper_class(program)

    raise QbraidError(f"Error applying circuit wrapper to quantum program of type {type(program)}")


def device_wrapper(device_id: str):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        device_id: unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.providers.DeviceLikeWrapper`: A wrapped quantum device-like object

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

    devices_entrypoints = _get_entrypoints("qbraid.providers")

    del device_info["_id"]  # unecessary for sdk
    del device_info["statusRefresh"]
    del device_info["objRef"]
    vendor = device_info["vendor"].lower()
    ep = f"{vendor}.device"
    device_wrapper_class = devices_entrypoints[ep].load()
    return device_wrapper_class(**device_info)


def job_wrapper(qbraid_job_id: str):
    """Retrieve a job from qBraid API using job ID and return job wrapper object.

    Args:
        qbraid_job_id: qBraid Job ID

    Returns:
        :class:`~qbraid.providers.job.JobLikeWrapper`: A wrapped quantum job-like object

    """
    session = QbraidSession()
    job_lst = session.post(
        "/get-user-jobs", json={"qbraidJobId": qbraid_job_id, "numResults": 1}
    ).json()

    if len(job_lst) == 0:
        raise QbraidError(f"{qbraid_job_id} is not a valid job ID.")

    job_data = job_lst[0]

    try:
        qbraid_device_id = job_data["qbraidDeviceId"]
        qbraid_device = device_wrapper(qbraid_device_id)
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
