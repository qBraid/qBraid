from cirq import Circuit

from qbraid.devices import DeviceLikeWrapper
from .job import CirqEngineJobWrapper
from .result import CirqResultWrapper
from .._utils import CIRQ_PROVIDERS


class CirqSamplerWrapper(DeviceLikeWrapper):
    def __init__(self, name, provider, **fields):
        """Cirq ``Sampler`` wrapper class

        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            AttributeError: if input field not a valid options

        """
        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        pass

    def run(self, program, **options):
        """Samples from the given Circuit. By default, the `run_async` method invokes this method
        on another thread. So this method is supposed to be thread safe.

        Args:
            program: The circuit to sample from.
            **options:
                param_resolver: Parameters to run with the program.
                repetitions: The number of times to sample.

        Returns:
            Result for a run.

        """
        cirq_sampler = self.vendor_dlo
        cirq_result = cirq_sampler.run(program, **options)
        qbraid_result = CirqResultWrapper(cirq_result)
        return qbraid_result


class CirqEngineWrapper(DeviceLikeWrapper):
    def __init__(self, name, provider, **fields):
        """Cirq ``Engine`` wrapper class.

        Args:
            name (str): a Cirq supported device
            provider (str): the provider that this device comes from
            fields: kwargs for the values to use to override the default options.

        Raises:
            AttributeError: if input field not a valid options

        """
        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        pass

    def run(self, program: Circuit, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.

        Args:
            program: The Circuit to execute. If a circuit is provided, a moment by moment schedule
                will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            A single Result for this run.

        """
        return self.vendor_dlo.run(program, **kwargs)

    def run_sweep(self, program: Circuit, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.Creates

        In contrast to run, this runs across multiple parameter sweeps, and does not block until
        a result is returned.

        Args:
            program: The Circuit to execute. If a circuit is provided, a moment by moment schedule
                will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            An EngineJob. If this is iterated over it returns a list of
            TrialResults, one for each parameter sweep.

        """
        cirq_engine = self.vendor_dlo
        cirq_engine_job = cirq_engine.run_sweep(program, **kwargs)
        qbraid_job = CirqEngineJobWrapper(self, cirq_engine_job)
        return qbraid_job
