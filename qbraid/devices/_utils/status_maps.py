from qbraid.devices.enums import Status

BraketQuantumTask = {
    "CREATED": Status.INITIALIZING,
    "QUEUED": Status.QUEUED,
    "RUNNING": Status.RUNNING,
    "CANCELLING": Status.CANCELLING,
    "CANCELLED": Status.CANCELLED,
    "COMPLETED": Status.COMPLETED,
    "FAILED": Status.FAILED,
}

QiskitJob = {
    "JobStatus.INITIALIZING": Status.INITIALIZING,
    "JobStatus.QUEUED": Status.QUEUED,
    "JobStatus.VALIDATING": Status.VALIDATING,
    "JobStatus.RUNNING": Status.RUNNING,
    "JobStatus.CANCELLED": Status.CANCELLED,
    "JobStatus.DONE": Status.COMPLETED,
    "JobStatus.ERROR": Status.FAILED,
}

CirqGoogleEngine = {
    "Status.STATE_UNSPECIFIED": Status.INITIALIZING,
    "Status.READY": Status.QUEUED,
    "Status.RUNNING": Status.RUNNING,
    "Status.CANCELLING": Status.CANCELLING,
    "Status.CANCELLED": Status.CANCELLED,
    "Status.SUCCESS": Status.COMPLETED,
    "Status.FAILURE": Status.FAILED,
}