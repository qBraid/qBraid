"""BraketQuantumtaskWrapper Class"""

from qbraid.devices.google.result import CirqResultWrapper
from qbraid.devices.localjob import LocalJobWrapper
from datetime import datetime


class CirqLocalJobWrapper(LocalJobWrapper):
    """CirqLocalJobWrapper class. NOTE: This is a place-holder job class for consistency. In Cirq, calling the run
    method on a simulator returns a result object. However, for consistency with the job-like interfaces in AWS Braket
    and IBM Qiskit, we provide this place-holder job class so that run-time is procedure is identical for all devices."""

    def __init__(self, device, vendor_rlo):
        """Create a CirqSimulatorJob."""

        super().__init__(device, vendor_rlo)
        self.vendor_rlo = vendor_rlo
        self._id = str(self.vendor_rlo).replace(" ", "") + str(datetime.now()).split(" ")[1]

    @property
    def id(self):
        """Return a unique id identifying the job."""
        return self._id

    def metadata(self):
        """Return the metadata regarding the job."""
        return None

    def result(self):
        """Return the results of the job."""
        return CirqResultWrapper(self.vendor_rlo)
