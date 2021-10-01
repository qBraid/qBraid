"""Module for Cirq device-like object wrappers."""

from cirq import DensityMatrixSimulator, Sampler, Simulator

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.google.job import CirqEngineJobWrapper
from qbraid.devices.google.result import CirqResultWrapper


class CirqSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Simulator`` objects."""

    def __init__(self, device_info, **fields):
        """Create CirqSimulatorWrapper."""

        super().__init__(device_info, **fields)

    def _get_device(self, obj_ref, obj_arg):
        """Initialize a Google device."""
        if obj_ref == "Simulator":
            return Simulator()
        elif obj_ref == "DensityMatrixSimulator":
            return DensityMatrixSimulator()
        else:
            raise DeviceError(f"obj_ref {obj_ref} not found.")

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return "ONLINE"

    def run(self, run_input, *args, **kwargs):
        """Samples from the given Circuit.

        Args:
            run_input: The circuit, i.e. program, to sample from.

        Keyword Args:
            shots (int): The number of times to sample. Default is 1.

        Returns:
            qbraid.devices.google.CirqResultWrapper: The result like object for the run.

        """
        shots = kwargs.pop("shots") if "shots" in kwargs else 1
        run_input = self._compat_run_input(run_input)
        cirq_simulator = self.vendor_dlo
        cirq_result = cirq_simulator.run(run_input, repetitions=shots, *args, **kwargs)
        qbraid_result = CirqResultWrapper(cirq_result)
        return qbraid_result


class CirqEngineWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Engine`` objects. NOTE: Right now the CirqEngine only
    allows privelaged access, so this class has not been tested and is still in development.

    """

    def __init__(self, device_info, **kwargs):
        """Creat a CirqEngineWrapper."""

        super().__init__(device_info, **kwargs)

    def _get_device(self, obj_ref, obj_arg):
        """Initialize a Google credentialed device."""
        return NotImplementedError  # privelaged access

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return NotImplementedError

    def run(self, run_input, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.

        Args:
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment
              schedule will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the
                value specified will be used instead of what's set in the options object.

        Returns:
            qbraid.devices.google.CirqResultWrapper: The result for this run.

        """
        run_input = self._compat_run_input(run_input)
        cirq_engine = self.vendor_dlo
        cirq_result = cirq_engine.run(run_input, *args, **kwargs)
        qbraid_result = CirqResultWrapper(cirq_result)
        return qbraid_result

    def run_sweep(self, run_input, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.Creates

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
        run_input = self._compat_run_input(run_input)
        cirq_engine = self.vendor_dlo
        cirq_engine_job = cirq_engine.run_sweep(run_input, *args, **kwargs)
        qbraid_job = CirqEngineJobWrapper(self, cirq_engine_job)
        return qbraid_job
