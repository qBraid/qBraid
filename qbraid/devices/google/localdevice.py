"""Module for Cirq device-like object wrappers."""

from cirq import DensityMatrixSimulator, Simulator

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.google.result import CirqResultWrapper
from qbraid.devices.enums import DeviceStatus


class CirqSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Google Cirq ``Simulator`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create CirqSimulatorWrapper."""

        super().__init__(device_info, **kwargs)

    def _get_device(self):
        """Initialize a Google device."""
        if self._obj_ref == "Simulator":
            return Simulator()
        elif self._obj_ref == "DensityMatrixSimulator":
            return DensityMatrixSimulator()
        else:
            raise DeviceError(f"obj_ref {self._obj_ref} not found.")

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return DeviceStatus.ONLINE

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
        run_input, _ = self._compat_run_input(run_input)
        cirq_simulator = self.vendor_dlo
        cirq_result = cirq_simulator.run(run_input, repetitions=shots, *args, **kwargs)
        return CirqResultWrapper(cirq_result)
