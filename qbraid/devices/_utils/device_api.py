from datetime import datetime

from IPython.core.display import HTML, clear_output, display
from pymongo import MongoClient
from tqdm.notebook import tqdm

import qbraid


def _get_device_data(query):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    client = MongoClient(qbraid.MONGO_DB, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    cursor = collection.find(query)
    device_data = []
    tot_dev = 0
    ref_dev = 0
    tot_lag = 0
    for document in cursor:
        qbraid_id = document["qbraid_id"]
        name = document["name"]
        provider = document["provider"]
        status_refresh = document["status_refresh"]
        timestamp = datetime.now()
        lag = 0 if status_refresh is None else (timestamp - status_refresh).seconds
        if lag > 3600:
            clear_output(wait=True)
            print("Auto-refreshing status for queried devices" + "." * tot_dev, flush=True)
            device = qbraid.device_wrapper(qbraid_id)
            status = device.status.name
            collection.update_one(
                {"qbraid_id": qbraid_id},
                {"$set": {"status": status, "status_refresh": timestamp}},
                upsert=False,
            )
            lag = 0
            ref_dev += 1
        else:
            status = document["status"]
        tot_dev += 1
        tot_lag += lag
        device_data.append([provider, name, qbraid_id, status])
    cursor.close()
    client.close()
    if tot_dev == 0:
        return [], 0  # No results matching given criteria
    if ref_dev > 0:
        clear_output(wait=True)
        # print("All status up-to-date", flush=True)
        # print("\r", f"Auto-refreshed status for {ref_dev}/{tot_dev} queried devices", end="")
    device_data.sort()
    lag_minutes, _ = divmod(tot_lag / tot_dev, 60)
    return device_data, int(lag_minutes)


def refresh_devices():
    """Refreshes status for all qbraid supported devices. Runtime ~30 seconds."""
    client = MongoClient(qbraid.MONGO_DB, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    cursor = collection.find({})
    pbar = tqdm(total=35, leave=False)
    for document in cursor:
        if document["status_refresh"] is not None:  # None => internally not available at moment
            qbraid_id = document["qbraid_id"]
            device = qbraid.device_wrapper(qbraid_id)
            status = device.status.name
            collection.update_one(
                {"qbraid_id": qbraid_id},
                {"$set": {"status": status, "status_refresh": datetime.now()}},
                upsert=False,
            )
        pbar.update(1)
    pbar.close()
    cursor.close()
    client.close()


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
    device_data, lag = _get_device_data(input_query)
    # msg = "All status up-to-date" if lag == 0 else f"Avg status lag ~{lag} min"

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
