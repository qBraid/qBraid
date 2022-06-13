"""
Module defining CirqEngineWrapper Class

"""
# pylint: disable=unused-argument,unused-import

from qbraid.devices.device import DeviceLikeWrapper

from .job import CirqEngineJobWrapper
from .result import CirqResultWrapper


class CirqEngineWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Engine`` objects.

    NOTE: Right now the CirqEngine only allows privelaged access, so this class
    has not been tested and is still in development.

    """

    def _get_device(self):
        """Initialize a Google credentialed device (TODO)."""
        return NotImplementedError  # privelaged access

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self):
        """Return the status of this Device. (TODO).

        Returns:
            str: The status of this Device
        """
        return NotImplementedError

    def run(self, run_input, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine (TODO).

        Args:
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment
              schedule will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the
                value specified will be used instead of what's set in the options object.

        Returns:
            qbraid.devices.google.CirqResultWrapper: The result for this run.

        """
        # run_input, _ = self._compat_run_input(run_input)
        # cirq_engine = self.vendor_dlo
        # cirq_result = cirq_engine.run(run_input, *args, **kwargs)
        # return CirqResultWrapper(cirq_result)
        return NotImplementedError

    def run_sweep(self, run_input, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.Creates (TODO)

        In contrast to run, this runs across multiple parameter sweeps, and does not block until
        a result is returned.

        Args:
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment
            schedule will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the
                value specified will be used instead of what's set in the options object.

        Returns:
            An EngineJob. If this is iterated over it returns a list of
            TrialResults, one for each parameter sweep.

        """
        # run_input, qbraid_circuit = self._compat_run_input(run_input)
        # cirq_engine = self.vendor_dlo
        # cirq_engine_job = cirq_engine.run_sweep(run_input, *args, **kwargs)
        # return CirqEngineJobWrapper(self, qbraid_circuit, cirq_engine_job)
        return NotImplementedError

    def estimate_cost(self, circuit, shots=1024):
        """Estimate the cost of running the supplied circuit (TODO)."""
        return NotImplementedError
