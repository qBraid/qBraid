# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compatibility shim between qBraid's IQM runtime and the IQM SDK."""

from __future__ import annotations

from functools import lru_cache
from importlib import import_module
import json
from types import SimpleNamespace


@lru_cache(maxsize=1)
def load_iqm_symbols() -> SimpleNamespace:
    """Load the IQM symbols needed by qBraid at runtime."""
    try:
        iqm_client = import_module("iqm.iqm_client")
        iqm_pulse = import_module("iqm.pulse")
    except ImportError as err:
        raise ImportError(
            "IQM runtime support requires the optional 'iqm' dependencies to be installed."
        ) from err

    return SimpleNamespace(
        IQMClient=iqm_client.IQMClient,
        JobStatus=iqm_client.JobStatus,
        CircuitCompilationOptions=iqm_client.CircuitCompilationOptions,
        ExistingMoveHandlingOptions=iqm_client.ExistingMoveHandlingOptions,
        transpile_insert_moves=iqm_client.transpile_insert_moves,
        Circuit=iqm_pulse.Circuit,
        CircuitOperation=iqm_pulse.CircuitOperation,
    )


@lru_cache(maxsize=1)
def load_iqm_qiskit_symbols() -> SimpleNamespace:
    """Load qiskit adapter helpers shipped with ``iqm-client[qiskit]``."""
    try:
        qiskit_to_iqm = import_module("iqm.qiskit_iqm.qiskit_to_iqm")
        iqm_qiskit_job = import_module("iqm.qiskit_iqm.iqm_job")
    except ImportError as err:
        raise ImportError(
            "IQM qiskit support requires the optional 'iqm-client[qiskit]' dependencies to be installed."
        ) from err

    return SimpleNamespace(
        serialize_instructions=qiskit_to_iqm.serialize_instructions,
        format_measurement_results=iqm_qiskit_job.IQMJob._iqm_format_measurement_results,
    )


def list_quantum_computers(
    iqm_server_url: str,
    *,
    token: str | None = None,
    tokens_file: str | None = None,
    client_signature: str | None = None,
) -> tuple[str, ...]:
    """List the quantum computer aliases visible through an IQM server."""
    try:
        iqm_server_client = import_module("iqm.iqm_server_client.iqm_server_client")
        authentication = import_module("iqm.station_control.client.authentication")
        requests = import_module("requests")
    except ImportError as err:
        raise ImportError(
            "IQM runtime support requires the optional 'iqm' dependencies to be installed."
        ) from err

    root_url, _, _ = iqm_server_client._IQMServerClient.normalize_url(iqm_server_url, None)
    token_manager = authentication.TokenManager(token, tokens_file)
    auth_header_callback = token_manager.get_auth_header_callback()
    headers = {
        "User-Agent": iqm_server_client._IQMServerClient._create_signature(client_signature),
        "Accept": "application/json",
    }
    if auth_header_callback:
        headers["Authorization"] = auth_header_callback()

    response = requests.get(
        f"{root_url}/api/v1/quantum-computers",
        headers=headers,
        timeout=iqm_server_client.REQUESTS_TIMEOUT,
    )
    if not response.ok:
        try:
            response_json = response.json()
            error_message = response_json.get("message") or response_json["detail"]
        except (json.JSONDecodeError, KeyError):
            error_message = response.text

        error_class = iqm_server_client.map_from_status_code_to_error(response.status_code)
        raise error_class(error_message)

    payload = iqm_server_client.ListQuantumComputersResponse.model_validate_json(response.text)
    return tuple(qc.alias for qc in payload.quantum_computers)
