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

"""
Module for reading Quantinuum NEXUS device queue lengths.

``qnexus`` exposes no wrapper for the NEXUS remote-queue endpoint, so this calls it
through the authenticated client ``qnexus`` already owns rather than opening a second
session. The endpoint is documented in the NEXUS OpenAPI schema as
``GET /api/v6/remote_queue/{issuer}``, returning one ``DeviceQueueInfo``
(``issuer``, ``device_name``, ``queue_length``) per device.

It is keyed by *issuer*, not by device, so a caller refreshing many devices can fetch
them all in one request by passing several names — or none, for every Quantinuum
device the account can see.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.runtime.exceptions import ResourceNotFoundError

from ._transport import ensure_bounded_client, retry_transient

if TYPE_CHECKING:
    from collections.abc import Sequence

#: NEXUS route for per-device queue lengths, keyed by credential issuer.
QUEUE_ENDPOINT = "/api/v6/remote_queue/Quantinuum"


def queue_lengths(device_names: Sequence[str] | None = None) -> dict[str, int]:
    """Return a mapping of NEXUS device name to the number of jobs queued on it.

    Args:
        device_names: Restrict the query to these devices. Omit to return every
            Quantinuum device visible to the authenticated account.

    Returns:
        Device name mapped to queue length. Devices NEXUS does not report are absent
        rather than zero, so a caller can tell "nothing queued" from "no answer".

    Raises:
        ResourceNotFoundError: The endpoint could not be reached or refused the request.
    """
    # Imported lazily, as everywhere else in this package: ``qnexus`` is an optional
    # extra, so importing it at module scope would make the whole runtime package
    # unimportable without it.
    import qnexus as qnx  # pylint: disable=import-outside-toplevel

    ensure_bounded_client()

    params = {"device_names": list(device_names)} if device_names else None
    response = retry_transient(
        lambda: qnx.client.get_nexus_client().get(QUEUE_ENDPOINT, params=params)
    )
    if response.status_code != 200:
        raise ResourceNotFoundError(
            f"NEXUS queue lengths unavailable (HTTP {response.status_code})."
        )

    # ``device_name`` and ``queue_length`` are both required by the schema, but a field
    # added or renamed upstream should degrade to "no answer for this device" rather
    # than raising in the middle of a refresh over every device.
    lengths: dict[str, int] = {}
    for entry in response.json():
        name = entry.get("device_name")
        length = entry.get("queue_length")
        if isinstance(name, str) and isinstance(length, int):
            lengths[name] = length
    return lengths
