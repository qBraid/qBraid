"""QiskitJobWrapper Class"""

from qbraid.devices.ibm import QiskitResultWrapper
from qbraid.devices.localjob import LocalJobWrapper


class QiskitBasicAerJobWrapper(LocalJobWrapper):
    """Wrapper class for IBM Qiskit ``Job`` objects."""

    def __init__(self, device, vendor_jlo):
        """Create a ``QiskitJobWrapper`` object."""
        super().__init__(device, vendor_jlo)

    @property
    def id(self):
        """Return a unique id identifying the job."""
        return self.vendor_jlo.jo_id()

    def metadata(self):
        """Return the metadata regarding the job."""
        return self.vendor_jlo.metadata

    def result(self):
        """Return the results of the job."""
        return QiskitResultWrapper(self.vendor_jlo.result())
