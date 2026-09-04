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

Kept free of provider/device/job imports so the provider and the job can both build a connection
without a circular import.

Authentication follows QPerfect's documented flow: a refresh token when one is available,
otherwise an account login whose token is kept for later connections in the same process.
See https://docs.qperfect.io/mimiqcircuits-python/manual/remote_execution.html.

MIMIQ tokens last about a day, so a stored one is best-effort. A rejected token falls back to a
credentials login rather than failing the call.

"""

from __future__ import annotations

import logging
import os

from mimiqcircuits import MimiqConnection
from mimiqlink import QPERFECT_CLOUD

logger = logging.getLogger(__name__)

TOKEN_ENV_VAR = "QPERFECT_API_TOKEN"
USERNAME_ENV_VAR = "QPERFECT_USERNAME"
PASSWORD_ENV_VAR = "QPERFECT_PASSWORD"
URL_ENV_VAR = "QPERFECT_BASE_URL"


def resolve_url(url: str | None = None) -> str:
    """Return the MIMIQ cloud URL, falling back to ``QPERFECT_BASE_URL`` then the public cloud."""
    return url or os.getenv(URL_ENV_VAR) or QPERFECT_CLOUD


def resolve_account(
    username: str | None = None, password: str | None = None
) -> tuple[str, str] | None:
    """Return the MIMIQ account credentials, or ``None`` when they are not configured.

    Args:
        username: MIMIQ account email. Falls back to ``QPERFECT_USERNAME``.
        password: MIMIQ account password. Falls back to ``QPERFECT_PASSWORD``.

    Returns:
        The ``(username, password)`` pair, or ``None`` if neither half is set.

    Raises:
        ValueError: If exactly one half is set. Falling through would authenticate as something
            the caller did not ask for.
    """
    username = username or os.getenv(USERNAME_ENV_VAR)
    password = password or os.getenv(PASSWORD_ENV_VAR)
    if username and password:
        return username, password
    if username or password:
        missing = PASSWORD_ENV_VAR if username else USERNAME_ENV_VAR
        raise ValueError(
            f"Incomplete QPerfect account credentials: {missing} is not set. "
            f"Set both {USERNAME_ENV_VAR} and {PASSWORD_ENV_VAR}, or pass username= and password=."
        )
    return None


def _publish_token(connection: MimiqConnection) -> None:
    """Record the refresh token a credentials login minted, for later connections.

    Current process only: nothing is written to disk, so this does not survive a restart.
    """
    token = getattr(connection.connection, "refresh_token", None)
    if token:
        os.environ[TOKEN_ENV_VAR] = token


def build_connection(
    token: str | None = None,
    *,
    url: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> MimiqConnection:
    """Build and authenticate a MIMIQ connection.

    Tries the refresh token first, then account credentials. A credentials login publishes its
    refresh token to ``QPERFECT_API_TOKEN`` for the next connection in this process.

    Args:
        token: A MIMIQ refresh token. Falls back to ``QPERFECT_API_TOKEN``.
        url: The MIMIQ cloud URL. Falls back to ``QPERFECT_BASE_URL`` then the public cloud.
        username: MIMIQ account email. Falls back to ``QPERFECT_USERNAME``.
        password: MIMIQ account password. Falls back to ``QPERFECT_PASSWORD``.

    Returns:
        An authenticated ``mimiqcircuits.MimiqConnection``.

    Raises:
        ValueError: If neither a token nor a complete set of credentials is available.
        ConnectionError: If a token is the only credential available and MIMIQ rejects it.
    """
    resolved_url = resolve_url(url)
    token = token or os.getenv(TOKEN_ENV_VAR)
    account = resolve_account(username, password)

    if token:
        connection = MimiqConnection(resolved_url)
        try:
            connection.connection.connectToken(token)
            return connection
        except Exception as err:  # pylint: disable=broad-except
            if account is None:
                raise
            # Expected roughly daily: MIMIQ tokens expire after a day and rotate on refresh.
            logger.info("MIMIQ rejected the refresh token (%s); logging in with credentials.", err)

    if account is None:
        raise ValueError(
            "QPerfect credentials are required. Set "
            f"{USERNAME_ENV_VAR} and {PASSWORD_ENV_VAR} (or pass username= and password=), "
            f"or supply a refresh token via {TOKEN_ENV_VAR} or token=."
        )

    connection = MimiqConnection(resolved_url)
    connection.connection.connectUser(*account)
    _publish_token(connection)
    return connection
