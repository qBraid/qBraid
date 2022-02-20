"""Module to retrieve the least busy IBMQ QPU"""
import os

from qiskit import IBMQ
from qiskit.providers.ibmq import least_busy

from qbraid.devices._utils import get_config


def ibmq_least_busy_qpu():
    """Return the qbraid id of the least busy IBMQ QPU."""
    IBMQ.enable_account(os.getenv('refresh-token'),os.getenv('API_URL')+'/ibm-routes?route=')
    group = get_config("group", "IBM")
    project = get_config("project", "IBM")
    provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
    backends = provider.backends(filters=lambda x: not x.configuration().simulator)
    backend_obj = least_busy(backends)
    ibm_id = backend_obj.__str__()
    qbraid_device_id = ibm_id[:3] + "_" + ibm_id[3:]
    return qbraid_device_id
