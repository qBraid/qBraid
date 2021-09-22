# pylint: skip-file

from IPython.core.display import HTML, display
from pymongo import MongoClient

from .aws_utils import AWS_CONFIG_PROMPT, AWS_DEVICES, aws_config_path
from .google_utils import GOOGLE_DEVICES
from .ibm_utils import IBMQ_CONFIG_PROMPT, IBM_DEVICES
from .user_config import get_config, set_config

SUPPORTED_DEVICES = {
    "aws": AWS_DEVICES,
    "google": GOOGLE_DEVICES,
    "ibm": IBM_DEVICES,
}

RUN_PACKAGE = {
    "aws": "braket",
    "google": "cirq",
    "ibm": "qiskit",
}

CONFIG_PROMPTS = {
    "aws": AWS_CONFIG_PROMPT,
    "google": None,
    "ibm": IBMQ_CONFIG_PROMPT,
}


def update_config(vendor):
    """Update the config associated with given vendor

    Args:
        vendor (str): a supported vendor

    """
    prompt_lst = CONFIG_PROMPTS[vendor]
    for prompt in prompt_lst:
        set_config(*prompt, update=True)
    return 0


def _mongodb_connect():
    """Connect to MongoDB and return client object.

    Note: Eventually this function will be replaced by a call to our qbraid API.

    """

    # Authentication string to be stored in our API
    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "devices?retryWrites=true&w=majority"
    )
    return MongoClient(conn_str, serverSelectionTimeoutMS=5000)


def _get_device_data(filter_dict):
    """Internal :meth:`qbraid.get_devices` helper function that connects with the MongoDB database
    and returns a list of devices that match the ``filter_dict`` filters. Each device is
    represented by its own length-3 list containing the device provider, name, and qbraid_id.

    Note: Right now each vendor has its own collection in MongoDB, so the vendor filter is handled
    seperatley. Eventually, we will want to list all of the devices under just one collection. By
    then adding a "vendor" field to each document, we can apply all filters at once. This will
    eliminate the need for the "vendor in filter_dict" if/else and the "vendor in vendors" for-loop.
    """

    client = _mongodb_connect()  # This line will be replaced by qBraid API call
    db = client["devices"]
    if "vendor" in filter_dict:
        vendors_input = filter_dict["vendor"]
        if isinstance(vendors_input, str):
            vendors = [vendors_input.lower()]
        elif isinstance(vendors_input, list):
            vendors = [x.lower() for x in vendors_input]
        else:
            raise TypeError("'vendor' must be of type <class 'str'> or <class 'list'>.")
        del filter_dict["vendor"]
    else:
        vendors = db.list_collection_names()
    device_data = []
    for vendor in vendors:
        collection = db[vendor]
        cursor = collection.find(filter_dict)
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
        html += "<tr><td colspan='3'; style='text-align:center'>No results matching " \
                "criteria</td></tr></table>"

    html += "</table>"

    return display(HTML(html))
