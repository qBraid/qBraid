# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Display information about quantum jobs in table view.

"""

from typing import Optional

try:
    from IPython.display import HTML, clear_output, display
except ImportError:  # pragma: no cover
    pass

from qbraid._display import running_in_jupyter


def _job_table_basic(data: list[str], message: str) -> None:
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


def _job_table_jupyter(data: list[str], message: Optional[str] = None, align: str = "right"):
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


def display_jobs_from_data(job_data: list[list[str]], message: Optional[str] = None):
    """Displays a list of quantum jobs submitted by user, tabulated by job ID,
    the date/time it was submitted, and status."""
    align = "center" if len(job_data) == 0 else "right"

    if not message:
        num_jobs = len(job_data)
        if num_jobs == 0:
            message = "No jobs found matching criteria."
        else:
            message = f"Displaying {num_jobs} job{'s' if num_jobs > 1 else ''}."

    if running_in_jupyter():
        return _job_table_jupyter(job_data, message, align=align)
    return _job_table_basic(job_data, message)
