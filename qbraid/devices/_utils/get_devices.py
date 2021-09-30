import qbraid
from IPython.core.display import HTML, display
from pymongo import MongoClient
from time import time
from tqdm.notebook import tqdm
import logging


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
    if seconds_diff > 3600:
        logging.info("Refreshing device status...")
        refresh_device_status()
        seconds_diff = 0
    refresh_minutes, _ = divmod(seconds_diff, 60)
    cursor = collection.find(filter_dict)
    device_data = []
    for document in cursor:
        qbraid_id = document["qbraid_id"]
        if qbraid_id != "last_refresh":
            name = document["name"]
            provider = document["provider"]
            status = document["status"]
            device_data.append([provider, name, qbraid_id, status])
    cursor.close()
    client.close()
    device_data.sort()
    return device_data, refresh_minutes


def refresh_device_status():
    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    pbar = tqdm(total=12, leave=False)
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
        {"qbraid_id": "last_refresh"}, {"$set": {"time_stamp": time_stamp, "num_devices": num_devices}}, upsert=False
    )
    client.close()


def get_devices(filter_dict=None):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID.

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
