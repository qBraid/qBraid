# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for top-level interfacing with the IBMQ API

"""
import re
from typing import Optional

from qiskit_ibm_provider import IBMProvider, least_busy
from qiskit_ibm_provider.accounts import AccountNotFoundError

from qbraid.api.exceptions import AuthError


def ibm_to_qbraid_id(name: str) -> str:
    """Converts IBM device name to qBraid device ID"""
    if name.startswith("ibm") or name.startswith("ibmq_"):
        return re.sub(r"^(ibm)(q)?_(.*)", r"\1_q_\3", name)
    return "ibm_q_" + name


def ibm_provider(token: Optional[str] = None) -> IBMProvider:
    """Get IBMQ AccountProvider"""
    try:
        if token is None:
            return IBMProvider()
        return IBMProvider(token=token)
    except (AccountNotFoundError, Exception) as err:
        raise AuthError from err


def ibm_least_busy_qpu() -> str:
    """Return the qBraid ID of the least busy IBMQ QPU."""
    provider = ibm_provider()
    backends = provider.backends(simulator=False, operational=True)
    backend = least_busy(backends)
    ibm_id = backend.name  # QPU name of form `ibm_*` or `ibmq_*`
    _, name = ibm_id.split("_")
    return f"ibm_q_{name}"
