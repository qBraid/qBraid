# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module to display information about quantum
jobs submitted through qBraid APIs.

"""
import sys
from typing import Any, Optional

try:
    from IPython.display import HTML, clear_output, display
except ImportError:
    pass

from qbraid_core import QbraidSession
from qbraid_core.services.quantum import QuantumClient, process_job_data


def _running_in_jupyter():
    """
    Determine if running within Jupyter.

    Credit: `braket.ipython_utils <https://github.com/aws/amazon-braket-sdk-python/
    blob/0d28a8fa89263daf5d88bc706e79200d8dc091a8/src/braket/ipython_utils.py>`_.

    Returns:
        bool: True if running in Jupyter, else False.
    """
    in_ipython = False
    in_ipython_kernel = False

    # if IPython hasn't been imported, there's nothing to check
    if "IPython" in sys.modules:
        get_ipython = sys.modules["IPython"].__dict__["get_ipython"]

        ip = get_ipython()
        in_ipython = ip is not None

    if in_ipython:
        in_ipython_kernel = getattr(ip, "kernel", None) is not None

    return in_ipython_kernel


def _display_basic(data: list[str], message: str) -> None:
    if len(data) == 0:
        print(message)
    else:
        headers = ["Job ID", "Submitted", "Status"]

        max_job_id_length = max(len(str(job_id)) for job_id, _, _ in data)
        max_job_id_length = max(max_job_id_length, len(headers[0]))

        header_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"
        separator_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"
        row_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"

        print(f"{message}:\n")
        print(header_format.format(*headers))

        separators = ["-" * len(header) for header in headers]
        print(separator_format.format(*separators))

        for job_id, timestamp, status in data:
            print(row_format.format(job_id, timestamp, status))


def _display_jupyter(data: list[str], message: Optional[str] = None, align: str = "right"):
    clear_output(wait=True)

    html = """<h3>Quantum Jobs</h3><table><tr>
    <th style='text-align:left'>qBraid ID</th>
    <th style='text-align:left'>Submitted</th>
    <th style='text-align:left'>Status</th></tr>
    """

    for job_id, timestamp, status_str in data:
        if status_str == "COMPLETED":
            color = "green"
        elif status_str == "FAILED":
            color = "red"
        elif status_str in [
            "INITIALIZING",
            "INITIALIZED",
            "CREATED",
            "QUEUED",
            "VALIDATING",
            "RUNNING",
        ]:
            color = "blue"
        else:
            color = "grey"

        status = f"<span style='color:{color}'>{status_str}</span>"

        html += f"""<tr>
        <td style='text-align:left'>{job_id}</td>
        <td style='text-align:left'>{timestamp}</td>
        <td style='text-align:left'>{status}</td></tr>
        """

    html += f"<tr><td colspan='4'; style='text-align:{align}'>{message}</td></tr>"

    html += "</table>"

    return display(HTML(html))


def display_jobs(filters: Optional[dict[str, Any]] = None):
    """Displays a list of quantum jobs submitted by user, tabulated by job ID,
    the date/time it was submitted, and status. You can specify filters to
    narrow the search by supplying a dictionary containing the desired criteria.

    **Request Syntax:**

    .. code-block:: python

        get_jobs(
            filters={
                'qbraidJobId': 'string',
                'vendorJobId': 'string',
                'qbraidDeviceId: 'string',
                'circuitNumQubits': 123,
                'circuitDepth': 123,
                'shots': 123,
                'status': 'string',
                'numResults': 123
            }
        )

    # pylint: disable=line-too-long
    **Filters:**

        * **qbraidJobId** (str): The qBraid ID of the quantum job
        * **vendorJobId** (str): The Job ID assigned by the software provider to whom the job was submitted
        * **qbraidDeviceId** (str): The qBraid ID of the device used in the job
        * **circuitNumQubits** (int): The number of qubits in the quantum circuit used in the job
        * **circuitDepth** (int): The depth the quantum circuit used in the job
        * **shots** (int): Number of shots used in the job
        * **status** (str): The status of the job
        * **numResults** (int): Maximum number of results to display. Defaults to 10 if not specified.

    Args:
        filters (dict): A dictionary containing any filters to be applied.
    """
    filters = filters or {}

    session = QbraidSession()

    if len(filters) == 0:
        client = QuantumClient(session=session)
        jobs = client.search_jobs()
    else:
        jobs = session.post("/get-user-jobs", json=filters).json()

    job_data, msg = process_job_data(jobs, filters)
    align = "center" if len(job_data) == 0 else "right"

    if _running_in_jupyter():
        return _display_jupyter(job_data, msg, align=align)
    return _display_basic(job_data, msg)
