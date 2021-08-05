"""Module for Cirq device-like object wrappers."""

from __future__ import annotations
from typing import TYPE_CHECKING

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.google.job import CirqEngineJobWrapper
from qbraid.devices.google.result import CirqResultWrapper
from qbraid.devices._utils import CIRQ_PROVIDERS

if TYPE_CHECKING:
    from cirq import Circuit


class CirqSamplerWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Sampler`` objects

    Args:
        name (str): a Cirq supported device
        provider (str): the provider that this device comes from
        fields: kwargs for the values to use to override the default options.

    Raises:
        DeviceError: if input field not a valid options

    """

    def __init__(self, name, provider, **fields):

        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

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
        cirq_sampler = self.vendor_dlo
        cirq_result = cirq_sampler.run(run_input, *args, **kwargs)
        qbraid_result = CirqResultWrapper(cirq_result)
        return qbraid_result


class CirqEngineWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Engine`` objects.

    Args:
        name (str): a Cirq supported device
        provider (str): the provider that this device comes from
        fields: kwargs for the values to use to override the default options.

    Raises:
        DeviceError: if input field not a valid options

    """

    def __init__(self, name, provider, **fields):

        super().__init__(name, provider, **fields)
        self._vendor = "Google"
        self.vendor_dlo = self._get_device_obj(CIRQ_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        return NotImplementedError

    def run(self, run_input: Circuit, *args, **kwargs):
        """Runs the supplied Circuit via Quantum Engine.

        Args:
            run_input: The Circuit to execute. If a circuit is provided, a moment by moment schedule
                will be used.
            kwargs: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Returns:
            A single Result for this run.

        """
        return self.vendor_dlo.run(run_input, **kwargs)

    def run_sweep(self, program: Circuit, *args, **kwargs):
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
        cirq_engine_job = cirq_engine.run_sweep(program, *args, **kwargs)
        qbraid_job = CirqEngineJobWrapper(self, cirq_engine_job)
        return qbraid_job
