"""BraketDeviceWrapper Class"""

from braket.aws import AwsDevice
from braket.devices import LocalSimulator

from qbraid.devices._utils import get_config
from qbraid.devices.aws.job import BraketQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.exceptions import DeviceError


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(device_info, **kwargs)
        if self.requires_cred:
            bucket = get_config("s3_bucket", "AWS")
            folder = get_config("s3_folder", "AWS")
            self._s3_location = (bucket, folder)
            self._arn = self._obj_arg
        else:
            self._s3_location = None
            self._arn = None

    def _get_device(self, obj_ref, obj_arg):
        """Initialize an AWS device."""
        if obj_ref == "AwsDevice":
            return AwsDevice(obj_arg)
        elif obj_ref == "LocalSimulator":
            return LocalSimulator(backend=obj_arg)
        else:
            raise DeviceError(f"obj_ref {obj_ref} not found.")

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self._obj_ref == "AwsDevice":
            return self.vendor_dlo.status
        return "ONLINE"

    def get_sampler(self, braket_default=False, embedding=True):
        """Returns BraketSampler created from device. Only compatible with D-Wave devices.

        Args:
            braket_default (optional, bool): If True, returns default BraketSampler. Defaults to
                False, returning BraketDWaveSampler.
            embedding (optional, bool): If True, uses EmbeddingComposite to automatically map the
                problem to the structure of the solver. If False, returns as sampler as-is.

        Returns:
            Sampler derived from device

        Raises:
            DeviceError if not a D-Wave annealing device.

        """
        if self.provider != "D-Wave":
            raise DeviceError("Sampler only available for D-Wave (annealing) devices")
        if braket_default:
            from braket.ocean_plugin import BraketSampler

            sampler = BraketSampler(self._s3_location, self._arn)
        else:
            from braket.ocean_plugin import BraketDWaveSampler

            sampler = BraketDWaveSampler(self._s3_location, self._arn)
        if embedding:
            from dwave.system.composites import EmbeddingComposite

            return EmbeddingComposite(sampler)
        else:
            return sampler

    def run(self, run_input, *args, **kwargs):
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input (Union[Circuit, Problem]): Specification of a task to run on device.
            kwargs: shots (int): The number of times to run the task on the device.

        Returns:
            :class:`~qbraid.devices.braket.job.BraketQuantumTaskWrapper`: The job like object for
                the run.

        """
        run_input = self._compat_run_input(run_input)
        braket_device = self.vendor_dlo
        if self.requires_cred:
            braket_quantum_task = braket_device.run(run_input, self._s3_location, *args, **kwargs)
        else:
            braket_quantum_task = braket_device.run(run_input, *args, **kwargs)
        qbraid_job = BraketQuantumTaskWrapper(self, braket_quantum_task)
        return qbraid_job
