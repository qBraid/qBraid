"""Module to retrieve the least busy IBMQ QPU"""

from qiskit import IBMQ
from qiskit.providers.ibmq import least_busy, IBMQProviderError

from qbraid.api import config_user


def ibmq_least_busy_qpu():
    """Return the qbraid id of the least busy IBMQ QPU."""
    if not IBMQ.active_account():
        IBMQ.load_account()
        # token = config_user.get_config("token", "ibmq", vendor="IBM", filename="qiskitrc")
        # base_url = config_user.get_config("url", "default", vendor="QBRAID", filename="qbraidrc")
        # api_url = f"{base_url}/ibm-routes?route="
        # IBMQ.enable_account(token, api_url)
    # provider = IBMQ.get_provider(hub="ibm-q", group="open", project="main")
    group = config_user.get_config("group", "ibmq", vendor="IBM", filename="qiskitrc")
    project = config_user.get_config("project", "ibmq", vendor="IBM", filename="qiskitrc")
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
