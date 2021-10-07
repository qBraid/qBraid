"""BraketLocalSimulatorWrapper Class"""

from braket.devices import LocalSimulator

from qbraid.devices.aws.localjob import BraketLocalQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus


class BraketLocalSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``LocalSimulator`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(device_info, **kwargs)

    def _get_device(self):
        """Initialize an AWS local simulator."""
        return LocalSimulator(backend=self._obj_arg)

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return DeviceStatus.ONLINE

    def run(self, run_input, *args, **kwargs):
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 0.

        Returns:
            qbraid.devices.aws.BraketLocalQuantumTaskWrapper: The job like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        local_quantum_task = self.vendor_dlo.run(run_input, *args, **kwargs)
        return BraketLocalQuantumTaskWrapper(self, local_quantum_task)
