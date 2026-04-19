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
from importlib.metadata import PackageNotFoundError, version
import platform
from types import SimpleNamespace
from urllib.parse import urlparse
import warnings

import numpy as np


def _create_client_signature(client_signature: str | None) -> str:
    """Mirror the IQM client User-Agent format without relying on private SDK helpers."""
    signature = platform.platform(terse=True)
    signature += f", python {platform.python_version()}"
    try:
        iqm_client_version = version("iqm-client")
    except PackageNotFoundError:
        iqm_client_version = "unknown"
    signature += f", IQMClient iqm-client {iqm_client_version}"
    if client_signature:
        signature += f", {client_signature}"
    return signature


def _normalize_server_url(
    iqm_server_url: str,
    *,
    configuration_error: type[Exception],
) -> str:
    """Validate and normalize an IQM server base URL."""
    if not iqm_server_url.isascii():
        raise configuration_error(f"Non-ASCII characters in URL: {iqm_server_url}")
    try:
        url = urlparse(iqm_server_url)
    except Exception as err:  # pragma: no cover - ``urlparse`` is very permissive.
        raise configuration_error(f"Invalid URL: {iqm_server_url}") from err

    if url.scheme not in {"http", "https"}:
        raise configuration_error(
            f"The URL schema has to be http or https. Incorrect schema in URL: {iqm_server_url}"
        )

    if url.hostname is None:
        raise configuration_error(f"Invalid URL: {iqm_server_url}")

    if url.path not in {"", "/"}:
        raise configuration_error(
            "The IQM Server URL must be a server base URL without a quantum computer path."
        )

    port_suffix = f":{url.port}" if url.port else ""
    return f"{url.scheme}://{url.hostname}{port_suffix}"


def _format_measurement_results(
    measurement_results: dict[str, list[list[int]]],
    requested_shots: int,
    expect_exact_shots: bool = True,
    *,
    measurement_key_cls,
) -> list[str]:
    """Convert IQM measurement payloads into qiskit-style bitstrings."""
    formatted_results: dict[int, np.ndarray] = {}
    shots = requested_shots if expect_exact_shots else 0

    for key, values in measurement_results.items():
        measurement_key = measurement_key_cls.from_string(key)
        result_array = np.asarray(values, dtype=int)
        current_shots = len(result_array)

        if current_shots == 0 and not expect_exact_shots:
            warnings.warn(
                "Received measurement results containing zero shots. "
                "In case you are using non-default heralding mode, this could be because of bad calibration."
            )
            result_array = np.array([], dtype=int)
        else:
            if result_array.ndim != 2 or result_array.shape[1] != 1:
                raise ValueError(
                    f"Measurement result {measurement_key} has the wrong shape {result_array.shape}, "
                    "expected (*, 1)"
                )
            result_array = result_array[:, 0]

        if expect_exact_shots and current_shots != requested_shots:
            raise ValueError(
                f"Expected {requested_shots} shots but got {current_shots} "
                f"for measurement result {measurement_key}"
            )

        if not expect_exact_shots:
            shots = current_shots

        classical_register = formatted_results.setdefault(
            measurement_key.creg_idx,
            np.zeros((current_shots, measurement_key.creg_len), dtype=int),
        )
        classical_register[:, measurement_key.clbit_idx] = result_array

    return [
        " ".join(
            "".join(map(str, classical_register[shot, :]))
            for _, classical_register in sorted(formatted_results.items())
        )[::-1]
        for shot in range(shots)
    ]


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
    except ImportError as err:
        raise ImportError(
            "IQM qiskit support requires the optional 'iqm-client[qiskit]' dependencies to be installed."
        ) from err

    return SimpleNamespace(
        serialize_instructions=qiskit_to_iqm.serialize_instructions,
        format_measurement_results=lambda measurement_results, requested_shots, expect_exact_shots=True: (
            _format_measurement_results(
                measurement_results,
                requested_shots,
                expect_exact_shots,
                measurement_key_cls=qiskit_to_iqm.MeasurementKey,
            )
        ),
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

    root_url = _normalize_server_url(
        iqm_server_url,
        configuration_error=authentication.ClientConfigurationError,
    )
    token_manager = authentication.TokenManager(token, tokens_file)
    auth_header_callback = token_manager.get_auth_header_callback()
    headers = {
        "User-Agent": _create_client_signature(client_signature),
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
        except (ValueError, KeyError):
            error_message = response.text

        error_class = iqm_server_client.map_from_status_code_to_error(response.status_code)
        raise error_class(error_message)

    payload = iqm_server_client.ListQuantumComputersResponse.model_validate_json(response.text)
    return tuple(qc.alias for qc in payload.quantum_computers)
