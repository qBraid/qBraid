# pylint: skip-file

from .config_user import get_config, update_config, verify_user
from .device_api import get_devices, refresh_devices, mongo_init_job, mongo_update_job
from .status_maps import BraketQuantumTask, QiskitJob, CirqGoogleEngine

STATUS_MAP = {
    "AWS": BraketQuantumTask,
    "IBM": QiskitJob,
    "Google": CirqGoogleEngine,
}
