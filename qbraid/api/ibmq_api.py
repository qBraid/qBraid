"""
Module for top-level interfacing with the IBMQ API

"""
from qiskit import IBMQ
from qiskit.providers.ibmq import AccountProvider, IBMQError, least_busy

from .exceptions import AuthError
from .config_specs import qiskitrc_path
from .config_user import get_config, verify_config


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
    ibm_id = str(backend_obj)
    qbraid_device_id = ibm_id[:3] + "_" + ibm_id[3:]
    return qbraid_device_id
