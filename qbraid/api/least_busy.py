"""
Module to retrieve the least busy IBMQ QPU.

"""
import os

from qiskit import IBMQ
from qiskit.providers.ibmq import IBMQProviderError, least_busy

from .config_user import get_config

qiskitrc_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")


def ibmq_least_busy_qpu() -> str:
    """Return the qBraid ID of the least busy IBMQ QPU."""
    if not IBMQ.active_account():
        IBMQ.load_account()
    provider = get_config("default_provider", "ibmq", filepath=qiskitrc_path)
    hub, group, project = provider.split("/")
    try:
        provider = IBMQ.get_provider(hub=hub, group=group, project=project)
    except IBMQProviderError:
        IBMQ.load_account()
        provider = IBMQ.get_provider(hub=hub, group=group, project=project)
    backends = provider.backends(filters=lambda x: not x.configuration().simulator)
    backend_obj = least_busy(backends)
    ibm_id = str(backend_obj)
    qbraid_device_id = ibm_id[:3] + "_" + ibm_id[3:]
    return qbraid_device_id
