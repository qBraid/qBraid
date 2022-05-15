"""Module to retrieve the least busy IBMQ QPU"""

import os

from qiskit import IBMQ
from qiskit.providers.ibmq import IBMQProviderError, least_busy

from .config_user import get_config

qiskitrc_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")


def ibmq_least_busy_qpu() -> str:
    """Return the qbraid ID of the least busy IBMQ QPU."""
    if not IBMQ.active_account():
        IBMQ.load_account()
        # token = get_config("token", "ibmq", filepath=qiskitrc_path)
        # base_url = get_config("url", "default")
        # api_url = f"{base_url}/ibm-routes?route="
        # IBMQ.enable_account(token, api_url)
    # provider = IBMQ.get_provider(hub="ibm-q", group="open", project="main")
    group = get_config("group", "IBM")
    project = get_config("project", "IBM")
    try:
        provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
    except IBMQProviderError:
        IBMQ.load_account()
        provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
    backends = provider.backends(filters=lambda x: not x.configuration().simulator)
    backend_obj = least_busy(backends)
    ibm_id = backend_obj.__str__()
    qbraid_device_id = ibm_id[:3] + "_" + ibm_id[3:]
    return qbraid_device_id
