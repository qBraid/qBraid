"""Module to retrieve the least busy IBMQ QPU"""

from qiskit import IBMQ
from qiskit.providers.ibmq import least_busy

from qbraid.api import config_user


def ibmq_least_busy_qpu():
    """Return the qbraid id of the least busy IBMQ QPU."""
    if not IBMQ.active_account():
        token = config_user.get_config("token", "sdk", qbraidrc=True)
        base_url = config_user.get_config("url", "QBRAID")
        api_url = f"{base_url}/ibm-routes?route="
        IBMQ.enable_account(token, api_url)
    provider = IBMQ.get_provider(hub="ibm-q", group="open", project="main")
    backends = provider.backends(filters=lambda x: not x.configuration().simulator)
    backend_obj = least_busy(backends)
    ibm_id = backend_obj.__str__()
    qbraid_device_id = ibm_id[:3] + "_" + ibm_id[3:]
    return qbraid_device_id
