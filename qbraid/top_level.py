from datetime import datetime
from time import time

import pkg_resources
from IPython.display import HTML, clear_output, display

from ._typing import QPROGRAM
from .api import ApiError, QbraidSession, ibmq_least_busy_qpu
from .exceptions import QbraidError
from .ipython_utils import running_in_jupyter

# pylint: disable=too-many-locals


def _get_entrypoints(group: str):
    """Returns a dictionary mapping each entry of ``group`` to its loadable entrypoint."""
    return {entry.name: entry for entry in pkg_resources.iter_entry_points(group)}


def circuit_wrapper(circuit: QPROGRAM):
    """Apply qbraid circuit  wrapper to a supported quantum program.

    This function is used to create a qBraid circuit-wrapper object, which can then be transpiled
    to any supported quantum circuit-building package. The input quantum circuit object must be
    an instance of a circuit object derived from a supported package.

    .. code-block:: python

        cirq_circuit = cirq.Circuit()
        q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]
        ...

    Please refer to the documentation of the individual qbraid circuit wrapper objects to see
    any additional arguments that might be supported.

    Args:
        circuit (QPROGRAM): a supported quantum circuit object

    Returns:
        :class:`~qbraid.transpiler.CircuitWrapper`: a qbraid circuit wrapper object

    Raises:
        QbraidError: If the input circuit is not a supported quantum program.

    """
    package = circuit.__module__.split(".")[0]
    ep = package.lower()

    transpiler_entrypoints = _get_entrypoints("qbraid.transpiler")

    if package in transpiler_entrypoints:
        circuit_wrapper_class = transpiler_entrypoints[ep].load()
        return circuit_wrapper_class(circuit)

    raise QbraidError(f"Error applying circuit wrapper to circuit of type {type(circuit)}")


def device_wrapper(qbraid_device_id: str, **kwargs):
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        qbraid_device_id (str): unique ID specifying a supported quantum hardware device/simulator

    Returns:
        :class:`~qbraid.devices.DeviceLikeWrapper`: a qbraid device wrapper object

    Raises:
        QbraidError: If ``qbraid_id`` is not a valid device reference.

    """
    if qbraid_device_id == "ibm_q_least_busy_qpu":
        qbraid_device_id = ibmq_least_busy_qpu()

    session = QbraidSession()
    device_info = session.get(
        "/public/lab/get-devices", params={"qbraid_id": qbraid_device_id}
    ).json()

    if isinstance(device_info, list):
        if len(device_info) == 0:
            raise QbraidError(f"{qbraid_device_id} is not a valid device ID.")
        device_info = device_info[0]

    if device_info is None:
        raise QbraidError(f"{qbraid_device_id} is not a valid device ID.")

    devices_entrypoints = _get_entrypoints("qbraid.devices")

    del device_info["_id"]  # unecessary for sdk
    del device_info["statusRefresh"]
    vendor = device_info["vendor"].lower()
    code = device_info.pop("_code")
    spec = ".local" if code == 0 else ".remote"
    ep = vendor + spec
    device_wrapper_class = devices_entrypoints[ep].load()
    return device_wrapper_class(device_info, **kwargs)


def retrieve_job(qbraid_job_id: str):
    """Retrieve a job from qBraid API using job ID and return job wrapper object."""
    qbraid_device = device_wrapper(qbraid_job_id.split("-")[0])
    vendor = qbraid_device.vendor.lower()
    if vendor == "google":
        raise QbraidError(f"API job retrieval not supported for {qbraid_device.id}")
    devices_entrypoints = _get_entrypoints("qbraid.devices")
    ep = vendor + ".job"
    job_wrapper_class = devices_entrypoints[ep].load()
    return job_wrapper_class(qbraid_job_id, device=qbraid_device)


def _print_progress(start, count):
    """Internal :func:`qbraid.refresh_devices` helper for
    printing quasi-progress-bar.

    Args:
        start (float): Time stamp marking beginning of function execution
        count (int): The total number of iterations completed so far
    """
    num_devices = 37  # i.e. number of iterations
    time_estimate = num_devices * 1.1  # estimated time for ~0.9 iters/s
    progress = count / num_devices
    elapsed_sec = int(time_estimate - (time() - start))
    stamp = f"{max(1, elapsed_sec)}s" if count > 0 else "1m"
    time_step = f"{stamp} remaining"
    dots = "." * count
    spaces = " " * (num_devices - count)
    percent = f"{int(progress*100)}%"
    clear_output(wait=True)
    print(f"{percent} | {dots} {spaces} | {time_step}", flush=True)


def refresh_devices():
    """Refreshes status for all qbraid supported devices. Requires credential for each vendor."""
    # pylint: disable=import-outside-toplevel

    session = QbraidSession()
    devices = session.get("/public/lab/get-devices", params={}).json()
    count = 0
    start = time()
    for document in devices:
        _print_progress(start, count)
        if document["statusRefresh"] is not None:  # None => internally not available at moment
            qbraid_id = document["qbraid_id"]
            device = device_wrapper(qbraid_id)
            status = device.status.name
            session.put("/lab/update-device", data={"qbraid_id": qbraid_id, "status": status})
        count += 1
    clear_output(wait=True)


def _get_device_data(query):
    """Internal :func:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    session = QbraidSession()
    devices = session.get("/public/lab/get-devices", params=query).json()

    if isinstance(devices, str):
        raise ApiError(devices)
    device_data = []
    tot_dev = 0
    # ref_dev = 0
    tot_lag = 0
    for document in devices:
        qbraid_id = document["qbraid_id"]
        name = document["name"]
        provider = document["provider"]
        status_refresh = document["statusRefresh"]
        timestamp = datetime.utcnow()
        lag = 0
        if status_refresh is not None:
            format_datetime = str(status_refresh)[:10].split("-") + str(status_refresh)[
                11:19
            ].split(":")
            format_datetime_int = [int(x) for x in format_datetime]
            mk_datime = datetime(*format_datetime_int)
            lag = (timestamp - mk_datime).seconds
        status = document["status"]
        tot_dev += 1
        tot_lag += lag
        device_data.append([provider, name, qbraid_id, status])
    if tot_dev == 0:
        return [], 0  # No results matching given criteria
    device_data.sort()
    lag_minutes, _ = divmod(tot_lag / tot_dev, 60)
    return device_data, int(lag_minutes)


def get_devices(filters=None, refresh=False):
    """get_devices(filters)
    Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria. Available filters
    include:

    * name (str)
    * vendor (str): AWS | IBM | Google
    * provider (str): AWS | IBM | Google | D-Wave | IonQ | Rigetti | OQC
    * type (str): QPU | Simulator
    * numberQubits (int)
    * paradigm (str): gate-based | quantum-annealer
    * requiresCred (bool): true | false
    * status (str): ONLINE | OFFLINE

    Here are a few example use cases:

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices(filters={"paradigm": "gate-based", "provider": "Google", "status": "ONLINE"})

        # Search for QPUs with at least 5 qubits that are available through AWS or IBM
        get_devices(filters={"type": "QPU", "numberQubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}})

        # Search for open-access simulators that have "Unitary" contained in their name
        get_devices(filters={"type": "Simulator", "name": {"$regex": "Unitary"}, "requiresCred": False})

    For a complete list of search operators, see `Query Selectors`__. To refresh the device status
    column, call :func:`~qbraid.refresh_devices`, and then re-run :func:`~qbraid.get_devices`.
    The bottom-right corner of the ``get_devices`` table indicates time since the last status
    refresh. Device status is auto-refreshed every hour.

    .. __: https://docs.mongodb.com/manual/reference/operator/query/#query-selectors

    Args:
        filters (optional, dict): a dictionary containing any filters to be applied.
        refresh (optional, bool): If True, calls refresh_devices before execution.

    """
    if refresh:
        refresh_devices()
    query = {} if filters is None else filters
    device_data, lag = _get_device_data(query)

    if not running_in_jupyter():
        device_dict = {}
        for data in device_data:
            provider = data[0]
            if provider not in device_dict:
                device_dict[provider] = {}
            qbraid_id = data[2]
            info = {"name": data[1], "status": data[3]}
            device_dict[provider][qbraid_id] = info
        return device_dict

    hours, minutes = divmod(lag, 60)
    min_10, _ = divmod(minutes, 10)
    min_display = min_10 * 10
    if hours > 0:
        if minutes > 30:
            msg = f"Device status updated {hours}.5 hours ago"
        else:
            hour_s = "hour" if hours == 1 else "hours"
            msg = f"Device status updated {hours} {hour_s} ago"
    else:
        if minutes < 10:
            min_display = minutes
        msg = f"Device status updated {min_display} minutes ago"

    html = """<h3>Supported Devices</h3><table><tr>
    <th style='text-align:left'>Provider</th>
    <th style='text-align:left'>Name</th>
    <th style='text-align:left'>qBraid ID</th>
    <th style='text-align:left'>Status</th></tr>
    """

    online = "<span style='color:green'>●</span>"
    offline = "<span style='color:red'>○</span>"

    for data in device_data:
        if data[3] == "ONLINE":
            status = online
        else:
            status = offline

        html += f"""<tr>
        <td style='text-align:left'>{data[0]}</td>
        <td style='text-align:left'>{data[1]}</td>
        <td style='text-align:left'><code>{data[2]}</code></td>
        <td>{status}</td></tr>
        """

    if len(device_data) == 0:
        html += (
            "<tr><td colspan='4'; style='text-align:center'>No results matching "
            "given criteria</td></tr>"
        )

    else:  # Design choice whether to display anything here or not
        html += f"<tr><td colspan='4'; style='text-align:right'>{msg}</td></tr>"

    html += "</table>"

    return display(HTML(html))
