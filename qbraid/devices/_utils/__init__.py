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


def _get_device_data():
    """Connect with MongoDB to retrieve device data"""

    conn_str = (
        "mongodb+srv://ryanjh88:Rq2bYCtKnMgh3tIA@cluster0.jkqzi.mongodb.net/"
        "devices?retryWrites=true&w=majority"
    )
    client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
    db = client["devices"]
    device_data = []
    vendors = ["aws", "google", "ibm"]
    for vendor in vendors:
        collection = db[vendor]
        cursor = collection.find({})
        for document in cursor:
            name = document["name"]
            provider = document["provider"]
            qbraid_id = document["qbraid_id"]
            device_data.append([provider, name, qbraid_id])
        cursor.close()
    client.close()
    device_data.sort()
    return device_data


def get_devices():
    """Prints all available devices, tabulated by provider, name, and qBraid ID."""

    device_data = _get_device_data()

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

    html += "</table>"

    return display(HTML(html))
