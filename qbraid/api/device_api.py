"""Module for interacting with qbraid device API"""

# pylint: disable=too-many-locals

from datetime import datetime

from IPython.display import HTML, display

import qbraid
from qbraid import api

# from IPython.display import clear_output


# from IPython.display import clear_output


def _get_device_data(query):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    devices = api.post("/public/lab/get-devices", json=query)
    if isinstance(devices, str):
        raise qbraid.QbraidError(devices)
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
        # if lag > 3600:  # update every hour
        #     clear_output(wait=True)
        #     print("Auto-refreshing status for queried devices" + "." * tot_dev, flush=True)
        #     device = qbraid.device_wrapper(qbraid_id)
        #     status = device.status.name
        #     qbraid.api.put(
        #         "/update-device",
        #         data={"qbraid_id": qbraid_id, "status": status},
        #         verify=False,
        #     )
        #     lag = 0
        #     ref_dev += 1
        # else:
        #     status = document["status"]
        status = document["status"]
        tot_dev += 1
        tot_lag += lag
        device_data.append([provider, name, qbraid_id, status])
    if tot_dev == 0:
        return [], 0  # No results matching given criteria
    # if ref_dev > 0:
    #     clear_output(wait=True)
    #     # print("All status up-to-date", flush=True)
    #     # print("\r", f"Auto-refreshed status for {ref_dev}/{tot_dev} queried devices", end="")
    device_data.sort()
    lag_minutes, _ = divmod(tot_lag / tot_dev, 60)
    return device_data, int(lag_minutes)


def refresh_devices():
    """Refreshes status for all qbraid supported devices. Requires credential for each vendor."""
    # pylint: disable=import-outside-toplevel
    from tqdm.notebook import tqdm

    devices = api.post("/public/lab/get-devices", json={})
    pbar = tqdm(total=35, leave=False)
    for document in devices:
        if document["statusRefresh"] is not None:  # None => internally not available at moment
            qbraid_id = document["qbraid_id"]
            device = qbraid.device_wrapper(qbraid_id)
            status = device.status.name
            api.put("/update-device", params={"qbraid_id": qbraid_id, "status": status})
        pbar.update(1)
    pbar.close()


def get_devices(query=None):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria. Available filters
    include:

    * name (str)
    * vendor (str): AWS | IBM | Google
    * provider (str): AWS | IBM | Google | D-Wave | IonQ | Rigetti
    * type (str): QPU | Simulator
    * qubits (int)
    * paradigm (str): gate-based | quantum-annealer
    * requires_cred (bool): true | false
    * status (str): ONLINE | OFFLINE

    Here are a few example use cases:

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices({"paradigm": "gate-based", "provider": "Google", "status": "ONLINE"})

        # Search for QPUs with at least 5 qubits that are available through AWS or IBM
        get_devices({"type": "QPU", "qubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}})

        # Search for open-access simulators that have "Unitary" contained in their name
        get_devices({"type": "Simulator", "name": {"$regex": "Unitary"}, "requires_cred": False})

    For a complete list of search operators, see `Query Selectors`__. To refresh the device status
    column, call :func:`~qbraid.refresh_devices`, and then re-run :func:`~qbraid.get_devices`.
    The bottom-right corner of the ``get_devices`` table indicates time since the last status
    refresh. Device status is auto-refreshed every hour.

    .. __: https://docs.mongodb.com/manual/reference/operator/query/#query-selectors

    Args:
        query (optional, dict): a dictionary containing any filters to be applied.

    """
    input_query = {} if query is None else query
    device_data, _ = _get_device_data(input_query)
    # device_data, lag = _get_device_data(input_query)
    # hours, minutes = divmod(lag, 60)
    # min_10, _ = divmod(minutes, 10)
    # min_display = min_10 * 10
    # if hours > 0:
    #     if minutes > 30:
    #         msg = f"Device status updated {hours}.5 hours ago"
    #     else:
    #         hour_s = "hour" if hours == 1 else "hours"
    #         msg = f"Device status updated {hours} {hour_s} ago"
    # else:
    #     if minutes < 10:
    #         min_display = minutes
    #     msg = f"Device status updated {min_display} minutes ago"

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

    # else:  # Design choice whether to display anything here or not
    #     html += f"<tr><td colspan='4'; style='text-align:right'>{msg}</td></tr>"

    html += "</table>"

    return display(HTML(html))
