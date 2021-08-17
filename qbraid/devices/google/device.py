"""Module for Cirq device-like object wrappers."""

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.google.job import CirqEngineJobWrapper
from qbraid.devices.google.result import CirqResultWrapper


class CirqSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Simulator`` objects."""

    def __init__(self, name, provider, **fields):
        """Create CirqSimulatorWrapper

        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            DeviceError: if input field not a valid options

        """
        super().__init__(name, provider, vendor="google", **fields)

    def _init_cred_device(self, device_ref):
        """Initialize a Google credentialed device."""
        raise DeviceError("Initializing a ``cirq.Simulator`` does not require credentials.")

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""

    def run(self, run_input, *args, **kwargs):
        """Samples from the given Circuit. By default, the `run_async` method invokes this method
        on another thread. So this method is supposed to be thread safe.

        Args:
            run_input: The circuit, i.e. program, to sample from.
            kwargs:
                param_resolver: Parameters to run with the program.
                repetitions (int): The number of times to sample.

        Returns:
            Result for a run.

        """
        run_input = self._compat_run_input(run_input)
        cirq_simulator = self.vendor_dlo
        cirq_result = cirq_simulator.run(run_input, *args, **kwargs)
        qbraid_result = CirqResultWrapper(cirq_result)
        return qbraid_result


class CirqEngineWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Engine`` objects. NOTE: Right now the CirqEngine only allows
    privelaged access, so this class has not been tested.

    """

    def __init__(self, name, provider, **fields):
        """Creat a CirqEngineWrapper

        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            DeviceError: if input field not a valid options

        """
        super().__init__(name, provider, vendor="google", **fields)

    def _init_cred_device(self, device_ref):
        """Initialize a Google credentialed device."""
        return NotImplementedError  # privelaged access

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        return NotImplementedError

    def run(self, run_input, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.

        Args:
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment schedule
                will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            A CirqResultWrapper representing the Result for this run.

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
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment schedule
                will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            An EngineJob. If this is iterated over it returns a list of
            TrialResults, one for each parameter sweep.

        """
        run_input = self._compat_run_input(run_input)
        cirq_engine = self.vendor_dlo
        cirq_engine_job = cirq_engine.run_sweep(run_input, *args, **kwargs)
        qbraid_job = CirqEngineJobWrapper(self, cirq_engine_job)
        return qbraid_job
