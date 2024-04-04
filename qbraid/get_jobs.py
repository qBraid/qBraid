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
Module to retrieve, update, and display information about quantum
jobs submitted through the qBraid SDK.

"""

import warnings
from typing import Any, Dict, List, Optional

try:
    from IPython.display import HTML, clear_output, display
except ImportError:
    pass

from qbraid_core import QbraidSession
from qbraid_core.services.quantum import QuantumClient, process_job_data

from ._display import running_in_jupyter, update_progress_bar


def _display_basic(data: List[str], message: str) -> None:
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


def _display_jupyter(data: List[str], message: Optional[str] = None, align: str = "right"):
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


def _refresh_jobs(job_data: List[str]) -> List[str]:
    """Refreshes the status of all quantum jobs in the list."""
    from qbraid.providers import QuantumJob  # pylint: disable=import-outside-toplevel

    count = 0
    num_jobs = len(job_data)
    job_data_refresh = []
    for job_id, created_at, status in job_data:
        count += 1
        progress = count / num_jobs
        update_progress_bar(progress)
        try:
            status_final = QuantumJob.status_final(status)
        except Exception:  # pylint: disable=broad-except
            status_final = True
        if not status_final:
            try:
                qbraid_job = QuantumJob.retrieve(job_id)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    status_obj = qbraid_job.status()
                status = status_obj.name
            except Exception:  # pylint: disable=broad-except
                pass
        job_data_refresh.append([job_id, created_at, status])

    return job_data_refresh


def get_jobs(filters: Optional[Dict[str, Any]] = None, refresh: bool = False, raw: bool = False):
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
        refresh (bool): If True, refreshes the status of all jobs before displaying them.
        raw (bool): If True, returns a list of job IDs instead of displaying the jobs.

    """
    filters = filters or {}

    session = QbraidSession()

    if len(filters) == 0:
        client = QuantumClient(session=session)
        jobs = client.search_jobs()
    else:
        jobs = session.post("/get-user-jobs", json=filters).json()

    job_data, msg = process_job_data(jobs, filters)

    if refresh:
        job_data = _refresh_jobs(job_data)

    if raw:
        return [job[0] for job in job_data]

    align = "center" if len(job_data) == 0 else "right"

    if running_in_jupyter():
        return _display_jupyter(job_data, msg, align=align)
    return _display_basic(job_data, msg)
