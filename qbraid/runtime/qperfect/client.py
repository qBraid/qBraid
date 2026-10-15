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
from requests import RequestException
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

TOKEN_ENV_VAR = "QPERFECT_API_TOKEN"
USERNAME_ENV_VAR = "QPERFECT_USERNAME"
PASSWORD_ENV_VAR = "QPERFECT_PASSWORD"
URL_ENV_VAR = "QPERFECT_BASE_URL"

# mimiqlink sets a 1 s connect timeout and no read timeout, so a request MIMIQ accepts and never
# answers blocks forever. That includes a login, which holds the provider's connection lock, and
# the token refresher, whose connection keeps reporting open while its token expires.
CONNECT_TIMEOUT_S = 1.0
READ_TIMEOUT_S = 60.0


class _TimeoutAdapter(HTTPAdapter):
    """Applies a default ``(connect, read)`` timeout to every request on a MIMIQ session.

    ``timeout=0`` still means no timeout, as in mimiqlink's own adapter: its job uploads pass it.
    """

    def __init__(self, timeout: tuple[float, float]):
        super().__init__()
        self._timeout = timeout

    def send(self, request, **kwargs):  # pylint: disable=arguments-differ
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self._timeout
        elif timeout == 0:
            kwargs["timeout"] = None
        return super().send(request, **kwargs)


def _new_connection(url: str) -> MimiqConnection:
    """Return an unauthenticated MIMIQ connection whose requests time out."""
    connection = MimiqConnection(url)
    adapter = _TimeoutAdapter((CONNECT_TIMEOUT_S, READ_TIMEOUT_S))
    session = connection.connection.session
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return connection


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
        requests.RequestException: If MIMIQ cannot be reached or does not answer in time.
    """
    resolved_url = resolve_url(url)
    token = token or os.getenv(TOKEN_ENV_VAR)
    account = resolve_account(username, password)

    if token:
        connection = _new_connection(resolved_url)
        try:
            connection.connection.connectToken(token)
            return connection
        except RequestException:
            # MIMIQ did not answer, rather than rejecting the token. A credentials login would
            # wait on the same host again while the caller holds the provider's connection lock.
            raise
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

    connection = _new_connection(resolved_url)
    connection.connection.connectUser(*account)
    _publish_token(connection)
    return connection
