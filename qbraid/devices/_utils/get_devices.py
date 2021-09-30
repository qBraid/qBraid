import qbraid
from IPython.core.display import HTML, display
from pymongo import MongoClient
from time import time
from tqdm.notebook import tqdm


def _get_device_data(filter_dict):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-4 list containing the device provider, name, qbraid_id,
    and status.
    """
    # Hard-coded authentication to be replaced with API call
    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    refresh_doc = collection.find_one({"qbraid_id": "last_refresh"})
    last_refresh = refresh_doc["time_stamp"]
    current_time = time()
    seconds_diff = current_time - last_refresh
    if seconds_diff > 3600:  # If it has been more than one hour since the last refresh
        print("Auto-refreshing")
        refresh_devices(auto_refresh=True)
        seconds_diff = 0
    refresh_minutes, _ = divmod(seconds_diff, 60)
    cursor = collection.find(filter_dict)
    device_data = []
    for document in cursor:
        qbraid_id = document["qbraid_id"]
        if qbraid_id != "last_refresh":  # last_refresh is its own document in MongoDB
            name = document["name"]
            provider = document["provider"]
            status = document["status"]
            device_data.append([provider, name, qbraid_id, status])
    cursor.close()
    client.close()
    device_data.sort()
    return device_data, refresh_minutes


def refresh_devices(auto_refresh=False):
    """Refreshes device status, seen in :func:`~qbraid.get_devices` output.
    Runtime ~20 seconds, with progress given by blue status bar."""

    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    desc = "Auto-refresh" if auto_refresh else ""
    pbar = tqdm(total=12, desc=desc, leave=False)
    cursor = collection.find({"type": "QPU", "vendor": {"$in": ["AWS", "IBM"]}})
    num_devices = 0
    for document in cursor:
        mongo_id = document["_id"]
        qbraid_id = document["qbraid_id"]
        device = qbraid.device_wrapper(qbraid_id)
        status = device.status
        collection.update_one({'_id': mongo_id}, {"$set": {"status": status}}, upsert=False)
        pbar.update(1)
        num_devices += 1
    cursor.close()
    pbar.close()
    time_stamp = time()
    collection.update_one(
        {"qbraid_id": "last_refresh"},
        {"$set": {"time_stamp": time_stamp, "num_devices": num_devices}},
        upsert=False
    )
    client.close()


def get_devices(filter_dict=None):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria. Available filters
    include but are not limited to:

    * name (str)
    * vendor (str): AWS | IBM | Google
    * provider (str): AWS | IBM | Google | D-Wave | IonQ | Rigetti
    * type (str): QPU | Simulator
    * qubits (int)
    * paradigm (str): gate-based | quantum-annealer
    * requires_cred (bool): true | false
    * status (str): ONLINE | OFFLINE

    Here are a few example ``get_devices`` arguments using the above filters:

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices({"paradigm": "gate-based", "provider": "Google", "status": "ONLINE"})

        # Search for QPUs with at least 5 qubits available through AWS or IBM
        get_devices({"type": "QPU", "qubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}})

        # Search for open-access simulators that have "Unitary" contained in their name
        get_devices({"type": "Simulator", "name": {"$regex": "Unitary"}, "requires_cred": False})

    For a complete list of search operators, see
    `Query Selectors`<https://docs.mongodb.com/manual/reference/operator/query/#query-selectors>.
    To refresh the device status column, call :func:`~qbraid.refresh_devices`, and then
    re-run :func:`~qbraid.get_devices`. The bottom-right corner of the ``get_devices`` table
    indicates time since the last status refresh. Device status is auto-refreshed every hour.

    Args:
        filter_dict (optional, dict): a dictionary containing any filters to be applied.

    """

    filter_dict = {} if filter_dict is None else filter_dict
    device_data, refresh_minutes = _get_device_data(filter_dict)
    last_refresh = "< 1" if refresh_minutes == 0 else "~" + str(int(refresh_minutes))

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
    else:
        html += (
            f"<tr><td colspan='4'; style='text-align:right'>Status last refreshed "
            f"{last_refresh} min ago</td></tr>"
        )

    html += "</table>"

    return display(HTML(html))
