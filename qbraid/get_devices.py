# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=consider-using-f-string

"""
Module to retrieve, update, and display information about devices
supported by the qBraid SDK.

"""
from typing import Any, Dict, List, Optional

try:
    from IPython.display import HTML, clear_output, display
except ImportError:
    pass

from qbraid_core import QbraidSession
from qbraid_core.services.quantum import QuantumClient, process_device_data

from ._display import running_in_jupyter, update_progress_bar


def _display_basic(data: List[str], message: str):
    if len(data) == 0:
        print(message)
    else:
        print(f"{message}\n")
        print("{:<35} {:<15}".format("Device ID", "Status"))
        print("{:<35} {:<15}".format("-" * 9, "-" * 6))
        for _, _, device_id, status in data:
            print("{:<35} {:<15}".format(device_id, status))


def _display_jupyter(data: List[str], message: Optional[str] = None, align: str = "right"):
    clear_output(wait=True)

    html = """<h3>Supported Devices</h3><table><tr>
    <th style='text-align:left'>Provider</th>
    <th style='text-align:left'>Name</th>
    <th style='text-align:left'>qBraid ID</th>
    <th style='text-align:left'>Status</th></tr>
    """

    status_icon = {
        "ONLINE": "<span style='color:green'>●</span>",
        "OFFLINE": "<span style='color:red'>○</span>",
        "RETIRED": "<span style='color:grey'>○</span>",
    }

    for item in data:
        if len(item) != 4:
            raise ValueError(
                f"Invalid data entry: {item}. Expected length-4 list containing: "
                "provider, name, qbraid_id, status."
            )

        provider, name, qbraid_id, status_str = item

        try:
            status = status_icon[status_str.upper()]
        except KeyError as err:
            raise ValueError(
                f"Invalid status: {status_str}. Must be one of {status_icon.keys()}."
            ) from err

        html += f"""<tr>
        <td style='text-align:left'>{provider}</td>
        <td style='text-align:left'>{name}</td>
        <td style='text-align:left'><code>{qbraid_id}</code></td>
        <td>{status}</td></tr>
        """

    if message:
        html += f"<tr><td colspan='4'; style='text-align:{align}'>{message}</td></tr>"

    html += "</table>"

    return display(HTML(html))


def _refresh_devices() -> None:
    """Refreshes status for all qbraid supported devices. Requires credential for each vendor."""
    # pylint: disable-next=import-outside-toplevel
    from qbraid.providers import QbraidProvider

    client = QuantumClient()
    provider = QbraidProvider(client=client)
    devices = client.search_devices()
    count = 0
    num_devices = len(devices)  # i.e. number of iterations
    for document in devices:
        progress = count / num_devices
        update_progress_bar(progress)
        if document["statusRefresh"] is not None:  # None => internally not available at moment
            qbraid_id = document["qbraid_id"]
            try:
                device = provider.get_device(qbraid_id)
                status = device.status().name
                client.update_device(data={"qbraid_id": qbraid_id, "status": status})
            except Exception:  # pylint: disable=broad-except
                pass

        count += 1
    update_progress_bar(1)
    print()


def get_devices(filters: Optional[Dict[str, Any]] = None, refresh: bool = False):
    """Displays a list of all supported devices matching given filters, tabulated by provider,
    name, and qBraid ID. Each device also has a status given by a solid green bubble or a hollow
    red bubble, indicating that the device is online or offline, respectively. You can narrow your
    device search by supplying a dictionary containing the desired criteria.

    **Request Syntax:**

    .. code-block:: python

        get_devices(
            filters={
                'name': 'string',
                'vendor': 'AWS'|'IBM',
                'provider: 'AWS'|'IBM'|'IonQ'|'Rigetti'|'OQC'|'QuEra',
                'type': 'QPU'|'SIMULATOR',
                'numberQubits': 123,
                'paradigm': 'gate-based'|'quantum-annealer'|'AHS'|'continuous-variable',
                'status': 'ONLINE'|'OFFLINE'|'RETIRED'
            }
        )

    **Filters:**

        * **name** (str): Name quantum device name
        * **vendor** (str): Company whose software facilitaces access to quantum device
        * **provider** (str): Company providing the quantum device
        * **type** (str): If the device is a quantum simulator or hardware
        * **numberQubits** (int): The number of qubits in quantum device
        * **paradigm** (str): The quantum model through which the device operates
        * **status** (str): Availability of device

    **Examples:**

    .. code-block:: python

        from qbraid import get_devices

        # Search for gate-based devices provided by Google that are online/available
        get_devices(
            filters={"paradigm": "gate-based", "provider": "IBM", "status": "ONLINE"}
        )

        # Search for QPUs with at least 5 qubits that are available through AWS or IBM
        get_devices(
            filters={"type": "QPU", "numberQubits": {"$gte": 5}, "vendor": {"$in": ["AWS", "IBM"]}}
        )

        # Search for state vector simulators by filtering for device ID's containing string "sv".
        get_devices(
            filters={"type": "SIMULATOR", "qbraid_id": {"$regex": "sv"}}
        )

    For a complete list of search operators, see `Query Selectors`__. To refresh the device
    status column, call :func:`~qbraid.get_devices` with ``refresh=True`` keyword argument.
    The bottom-right corner of the device table indicates time since the last status refresh.

    .. __: https://docs.mongodb.com/manual/reference/operator/query/#query-selectors

    Args:
        filters: A dictionary containing any filters to be applied.
        refresh: If True, calls :func:`~qbraid.refresh_devices` before execution.

    """
    if refresh:
        _refresh_devices()

    session = QbraidSession()
    query = {} if filters is None else filters

    # forward compatibility for casing transition
    if query.get("type") == "SIMULATOR":
        query["type"] = "Simulator"

    if len(query) == 0:
        client = QuantumClient(session=session)
        devices = client.search_devices()
    else:
        # get-devices must be a POST request with kwarg `json` (not `data`) to
        # encode the query. This is because certain queries contain regular
        # expressions which cannot be encoded in GET request `params`.
        devices = session.post("/public/lab/get-devices", json=query).json()

    device_data, msg = process_device_data(devices)
    align = "center" if len(device_data) == 0 else "right"

    if running_in_jupyter():
        return _display_jupyter(device_data, msg, align=align)
    return _display_basic(device_data, msg)
