# Copyright 2023 qBraid
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
