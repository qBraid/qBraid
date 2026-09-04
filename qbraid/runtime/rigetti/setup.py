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

# pylint: disable=no-name-in-module

"""
Setup utilities for the Rigetti provider: constants, error class, and
helper functions for QCS client construction and local process management.

"""

from __future__ import annotations

import os
import shutil
import socket
import time
from pathlib import Path

from qcs_sdk.client import AuthServer, OAuthSession, QCSClient, RefreshToken

from qbraid.runtime.exceptions import QbraidRuntimeError

DEFAULT_GRPC_API_URL = "https://grpc.qcs.rigetti.com"
DEFAULT_QUILC_URL = "tcp://127.0.0.1:5555"
DEFAULT_QVM_URL = "http://127.0.0.1:5000"
DEFAULT_QUILC_PORT = 5555
DEFAULT_QVM_PORT = 5000


class RigettiProviderError(QbraidRuntimeError):
    """Class for errors raised during Rigetti provider setup."""


def build_oauth_session(
    refresh_token: str,
    client_id: str | None = None,
    issuer: str | None = None,
) -> OAuthSession:
    """Build an ``OAuthSession`` from credentials.

    When both ``client_id`` and ``issuer`` are provided, a custom
    ``AuthServer`` is constructed; otherwise ``AuthServer.default()``
    is used.
    """
    if client_id and issuer:
        auth_server = AuthServer(client_id=client_id, issuer=issuer)
    else:
        auth_server = AuthServer.default()

    return OAuthSession(
        RefreshToken(refresh_token=refresh_token),
        auth_server,
    )


def build_qcs_client(
    oauth_session: OAuthSession,
    *,
    grpc_api_url: str | None = None,
    quilc_url: str | None = None,
    qvm_url: str | None = None,
    api_url: str | None = None,
) -> QCSClient:
    """Build a ``QCSClient`` from a pre-constructed ``OAuthSession``.

    URL kwargs that are ``None`` are omitted so the qcs_sdk's own
    defaults apply. Callers that want to preserve specific URLs should
    pass them explicitly (e.g. when rebuilding a client to honour URL
    overrides).
    """
    kwargs: dict = {"oauth_session": oauth_session}
    if grpc_api_url is not None:
        kwargs["grpc_api_url"] = grpc_api_url
    if quilc_url is not None:
        kwargs["quilc_url"] = quilc_url
    if qvm_url is not None:
        kwargs["qvm_url"] = qvm_url
    if api_url is not None:
        kwargs["api_url"] = api_url

    return QCSClient(**kwargs)


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check whether a TCP port is already accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex((host, port)) == 0


def find_binary(name: str) -> Path | None:
    """Find a binary on PATH or in ~/.qbraid/rigetti/bin/."""
    which_result = shutil.which(name)
    if which_result:
        return Path(which_result)
    fallback = Path.home() / ".qbraid" / "rigetti" / "bin" / name
    if fallback.is_file() and os.access(fallback, os.X_OK):
        return fallback
    return None


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 15.0) -> None:
    """Block until a TCP port starts accepting connections or timeout elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.5)
    raise RigettiProviderError(f"Timed out waiting for port {port} on {host} after {timeout}s.")


def download_forest_sdk() -> None:
    """Stub: download and install quilc/qvm binaries.

    Full implementation deferred to a follow-up PR since it involves
    platform-specific installers (.pkg, .deb, .rpm, .msi).
    """
    raise RigettiProviderError(
        "quilc binary not found. Install the Forest SDK manually:\n"
        "  macOS:  Download from https://qcs.rigetti.com/sdk-downloads\n"
        "  Linux:  Download from https://qcs.rigetti.com/sdk-downloads\n"
        "  Docker: docker run --rm -p 5555:5555 rigetti/quilc -S\n"
        "Then re-run setup()."
    )
