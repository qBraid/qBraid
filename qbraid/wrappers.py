"""
Module containing top-level qbraid wrapper functionality. Each of these
functions utilize entrypoints via ``pkg_resources``.

"""
import pkg_resources

from ._qprogram import QUANTUM_PROGRAM
from .api import QbraidSession, ibmq_least_busy_qpu
from .exceptions import QbraidError


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


def circuit_wrapper(program: QUANTUM_PROGRAM):
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


def device_wrapper(qbraid_device_id: str):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        qbraid_device_id: unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.devices.DeviceLikeWrapper`: A wrapped quantum device-like object

    Raises:
        :class:`~qbraid.QbraidError`: If ``qbraid_id`` is not a valid device reference.

    """
    if qbraid_device_id == "ibm_q_least_busy_qpu":
        qbraid_device_id = ibmq_least_busy_qpu()

    session = QbraidSession()
    device_lst = session.get(
        "/public/lab/get-devices", params={"qbraid_id": qbraid_device_id}
    ).json()

    if len(device_lst) == 0:
        raise QbraidError(f"{qbraid_device_id} is not a valid device ID.")

    device_info = device_lst[0]

    devices_entrypoints = _get_entrypoints("qbraid.devices")

    del device_info["_id"]  # unecessary for sdk
    del device_info["statusRefresh"]
    vendor = device_info["vendor"].lower()
    code = device_info.pop("_code")
    spec = ".local" if code == 0 else ".remote"
    ep = vendor + spec
    device_wrapper_class = devices_entrypoints[ep].load()
    return device_wrapper_class(**device_info)


def job_wrapper(qbraid_job_id: str):
    """Retrieve a job from qBraid API using job ID and return job wrapper object.

    Args:
        qbraid_job_id: qBraid Job ID

    Returns:
        :class:`~qbraid.devices.job.JobLikeWrapper`: A wrapped quantum job-like object

    """
    session = QbraidSession()
    job_lst = session.post(
        "/get-user-jobs", json={"qbraidJobId": qbraid_job_id, "numResults": 1}
    ).json()

    if len(job_lst) == 0:
        raise QbraidError(f"{qbraid_job_id} is not a valid job ID.")

    job_data = job_lst[0]

    status_str = job_data["status"]
    vendor_job_id = job_data["vendorJobId"]
    qbraid_device_id = job_data["qbraidDeviceId"]
    qbraid_device = device_wrapper(qbraid_device_id)
    vendor = qbraid_device.vendor.lower()
    if vendor == "google":
        raise QbraidError(f"API job retrieval not supported for {qbraid_device.id}")
    devices_entrypoints = _get_entrypoints("qbraid.devices")
    ep = vendor + ".job"
    job_wrapper_class = devices_entrypoints[ep].load()
    return job_wrapper_class(
        qbraid_job_id, vendor_job_id=vendor_job_id, device=qbraid_device, status=status_str
    )
