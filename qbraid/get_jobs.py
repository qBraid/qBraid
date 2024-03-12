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
from typing import Any, Dict, List, Optional, Tuple

try:
    from IPython.display import HTML, clear_output, display
except ImportError:
    pass

from ._display import running_in_jupyter, update_progress_bar
from .api import QbraidSession
from .load_provider import job_wrapper


def _display_jobs_basic(data, msg):
    if len(data) == 0:
        print(msg)
    else:
        headers = ["Job ID", "Submitted", "Status"]

        max_job_id_length = max(len(str(job_id)) for job_id, _, _ in data)
        max_job_id_length = max(max_job_id_length, len(headers[0]))

        header_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"
        separator_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"
        row_format = "{:<" + str(max_job_id_length) + "} {:<25} {:<15}"

        print(f"{msg}:\n")
        print(header_format.format(*headers))

        separators = ["-" * len(header) for header in headers]
        print(separator_format.format(*separators))

        for job_id, timestamp, status in data:
            print(row_format.format(job_id, timestamp, status))


def _display_jobs_jupyter(data, msg):
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

    html += f"<tr><td colspan='4'; style='text-align:right'>{msg}</td></tr>"

    html += "</table>"

    return display(HTML(html))


def _get_jobs_data(
    query: Dict[str, Any],
    refresh: bool = False,
    session: Optional[QbraidSession] = None,
) -> Tuple[List[List[str]], str]:
    from qbraid.providers import QuantumJob  # pylint: disable=import-outside-toplevel

    session = QbraidSession() if not session else session
    jobs = session.post("/get-user-jobs", json=query).json()
    max_results = query.pop("numResults", 10)
    count = 0
    num_jobs = len(jobs)
    job_data = []
    for document in jobs:
        count += 1
        progress = count / num_jobs
        if refresh:
            update_progress_bar(progress)
        job_id = document.get("qbraidJobId", document.get("_id"))
        if job_id is None:
            continue
        created_at = document.get("createdAt")
        if created_at is None:
            timestamps = document.get("timestamps", {})
            created_at = timestamps.get("createdAt", timestamps.get("jobStarted"))
        status = document.get("qbraidStatus", document.get("status", "UNKNOWN"))
        try:
            status_final = QuantumJob.status_final(status)
        except Exception:  # pylint: disable=broad-except
            status_final = True
        if refresh and not status_final:
            try:
                qbraid_job = job_wrapper(job_id)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    status_obj = qbraid_job.status()
                status = status_obj.name
            except Exception:  # pylint: disable=broad-except
                pass
        job_data.append([job_id, created_at, status])

    if num_jobs == 0:  # Design choice whether to display anything here or not
        if len(query) == 0:
            msg = f"No jobs found for user {session.user_email}"
        else:
            msg = "No jobs found matching given criteria"
    elif num_jobs < max_results:
        msg = f"Displaying {num_jobs}/{num_jobs} jobs matching query"
    elif len(query) > 0:
        s = "s" if num_jobs > 1 else ""
        msg = f"Displaying {num_jobs} most recent job{s} matching query"
    else:
        msg = f"Displaying {num_jobs} most recent jobs"
    return job_data, msg


def get_jobs(
    filters: Optional[dict] = None,
    refresh: bool = False,
    raw: bool = False,
    session: Optional[QbraidSession] = None,
):  # pylint: disable=too-many-statements
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
        session (QbraidSession): A qBraid session object. If not provided, a new session will be created.

    """
    filters = filters or {}

    job_data, msg = _get_jobs_data(filters, refresh, session)

    if raw:
        job_ids = [job[0] for job in job_data]
        return job_ids

    if running_in_jupyter():
        return _display_jobs_jupyter(job_data, msg)
    return _display_jobs_basic(job_data, msg)
