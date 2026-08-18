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
Module defining the QPerfect (MIMIQ) connection helpers.

Kept free of provider/device/job imports so both the provider and the job can build an
authenticated connection from a token without a circular import.

"""

from __future__ import annotations

import os

from mimiqcircuits import MimiqConnection
from mimiqlink import QPERFECT_CLOUD


def resolve_token(token: str | None) -> str:
    """Return the QPerfect API token, falling back to the ``QPERFECT_API_TOKEN`` env var.

    Raises:
        ValueError: If no token is available.
    """
    token = token or os.getenv("QPERFECT_API_TOKEN")
    if not token:
        raise ValueError(
            "A QPerfect API token is required. Pass token=... or set the "
            "QPERFECT_API_TOKEN environment variable."
        )
    return token


def build_connection(token: str, *, url: str | None = None) -> MimiqConnection:
    """Build and authenticate a MIMIQ connection from an API token.

    Args:
        token: The QPerfect API token.
        url: The MIMIQ cloud URL. Falls back to ``QPERFECT_BASE_URL`` then the public cloud.

    Returns:
        An authenticated ``mimiqcircuits.MimiqConnection``.
    """
    resolved_url = url or os.getenv("QPERFECT_BASE_URL") or QPERFECT_CLOUD
    connection = MimiqConnection(resolved_url)
    connection.connection.connectToken(token)
    return connection
