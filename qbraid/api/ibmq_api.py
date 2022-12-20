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
from qiskit import IBMQ
from qiskit.providers.ibmq import AccountProvider, IBMQError, least_busy

from .config_data import qiskitrc_path
from .config_user import get_config, verify_config
from .exceptions import AuthError


def ibmq_get_provider() -> AccountProvider:
    """Get IBMQ AccountProvider"""
    verify_config("IBM")
    # token = get_config("token", "ibmq", filepath=qiskitrc_path)
    default = get_config("default_provider", "ibmq", filepath=qiskitrc_path)
    hub, group, project = default.split("/")
    if IBMQ.active_account():
        IBMQ.disable_account()
    try:
        IBMQ.load_account()
        return IBMQ.get_provider(hub=hub, group=group, project=project)
    except IBMQError as err:
        raise AuthError from err


def ibmq_least_busy_qpu() -> str:
    """Return the qBraid ID of the least busy IBMQ QPU."""
    provider = ibmq_get_provider()
    backends = provider.backends(simulator=False, operational=True)
    backend_obj = least_busy(backends)
    ibm_id = str(backend_obj)  # QPU name of form `ibm_*` or `ibmq_*`
    _, name = ibm_id.split("_")
    return f"ibm_q_{name}"
