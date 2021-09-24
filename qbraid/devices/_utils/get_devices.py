from IPython.core.display import HTML, display
from pymongo import MongoClient


def _get_device_data(filter_dict):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-3 list containing the device provider, name, and qbraid_id.
    """
    # Hard-coded autentication to be replaced with API call
    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "qbraid-sdk?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["qbraid-sdk"]
    collection = db["supported_devices"]
    cursor = collection.find(filter_dict)
    device_data = []
    for document in cursor:
        name = document["name"]
        provider = document["provider"]
        qbraid_id = document["qbraid_id"]
        device_data.append([provider, name, qbraid_id])
    cursor.close()
    client.close()
    device_data.sort()
    return device_data


def get_devices(filter_dict=None):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID.

    Args:
        filter_dict (optional, dict): a dictionary containing any filters to be applied.

    """

    filter_dict = {} if filter_dict is None else filter_dict
    device_data = _get_device_data(filter_dict)

    html = """<h3>Supported Devices</h3><table><tr>
    <th style='text-align:left'>Provider</th>
    <th style='text-align:left'>Name</th>
    <th style='text-align:left'>qBraid ID</th></tr>
    """

    for data in device_data:
        html += f"""<tr>
        <td style='text-align:left'>{data[0]}</td>
        <td style='text-align:left'>{data[1]}</td>
        <td style='text-align:left'><code>{data[2]}</code></td></tr>
        """

    if len(device_data) == 0:
        html += (
            "<tr><td colspan='3'; style='text-align:center'>No results matching "
            "given criteria</td></tr>"
        )

    html += "</table>"

    return display(HTML(html))
