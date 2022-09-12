"""
Module defining BraketLocalSimulatorWrapper Class

"""
from typing import TYPE_CHECKING

from braket.devices import LocalSimulator

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .localjob import BraketLocalQuantumTaskWrapper

if TYPE_CHECKING:
    import braket

    import qbraid


class BraketLocalSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``LocalSimulator`` objects."""

    def _get_device(self):
        """Initialize an AWS local simulator."""
        try:
            return LocalSimulator(backend=self._obj_arg)
        except ValueError as err:
            raise DeviceError("Device not found.") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self) -> "qbraid.devices.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        return DeviceStatus.ONLINE

    def run(
        self, run_input: "braket.circuits.Circuit", *args, **kwargs
    ) -> "qbraid.devices.aws.BraketLocalQuantumTaskWrapper":
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is ``0``.

        Returns:
            The job like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        local_quantum_task = self.vendor_dlo.run(run_input, *args, **kwargs)
        return BraketLocalQuantumTaskWrapper(self, local_quantum_task)

    def estimate_cost(self, circuit: "braket.circuits.Circuit", shots: int = 1024):
        """Estimate the cost of running a circuit on the device."""
        # TODO: Connect/ensure consistency with the cost estimator in the API.
        return 0.0
