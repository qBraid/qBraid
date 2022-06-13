"""
Module defining CirqEngineJobWrapper Class.

See `cirq-google/`__.

.. __: https://github.com/quantumlib/Cirq/blob/master/cirq-google/cirq_google/engine/engine_job.py

"""
# from cirq_google.engine.engine_job import EngineJob

from qbraid.devices.job import JobLikeWrapper


class CirqEngineJobWrapper(JobLikeWrapper):
    """Wrapper class for Google Cirq ``EngineJob`` objects."""

    def __init__(self, job_id, vendor_job_id=None, device=None, vendor_jlo=None):
        """Create a CirqEngineJobWrapper."""
        super().__init__(job_id, vendor_job_id, device, vendor_jlo)

    def _get_vendor_jlo(self):
        """Return the job like object that is being wrapped."""
        return NotImplementedError

    def _get_status(self):
        """Returns status from Cirq Engine Job object."""
        return self.vendor_jlo.status()

    def result(self):
        """Returns the job results, blocking until the job is complete."""
        return self.vendor_jlo.results()

    def cancel(self):
        """Cancel the job."""
        self.vendor_jlo.cancel()
