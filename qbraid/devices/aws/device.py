"""BraketDeviceWrapper Class"""

import warnings

from braket.aws import AwsDevice
from braket.ocean_plugin import BraketDWaveSampler, BraketSampler
from dwave.system.composites import EmbeddingComposite

from qbraid.devices._utils import get_config, init_job
from qbraid.devices.aws.job import BraketQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(device_info, **kwargs)
        bucket = get_config("s3_bucket", "AWS")
        folder = get_config("s3_folder", "AWS")
        self._s3_location = (bucket, folder)
        self._arn = self._obj_arg

    def _get_device(self):
        """Initialize an AWS device."""
        return AwsDevice(self._obj_arg)

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self.vendor_dlo.status == "OFFLINE":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

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
            DeviceError: If not a D-Wave annealing device.

        """
        if self.provider != "D-Wave":
            raise DeviceError("Sampler only available for D-Wave (annealing) devices")
        if braket_default:
            sampler = BraketSampler(self._s3_location, self._arn)
        else:
            sampler = BraketDWaveSampler(self._s3_location, self._arn)
        if embedding:
            return EmbeddingComposite(sampler)
        else:
            return sampler

    def run(self, run_input, *args, **kwargs):
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device.

        Returns:
            qbraid.devices.aws.BraketQuantumTaskWrapper: The job like object for the run.

        """
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        if "shots" not in kwargs and not run_input.result_types:
            warnings.warn(
                "No result types specified for circuit and shots=0. See "
                "`braket.circuit.result_types`. Defaulting to shots=1024 and continuing run.",
                UserWarning,
            )
            kwargs["shots"] = 1024
        aws_quantum_task = self.vendor_dlo.run(run_input, self._s3_location, *args, **kwargs)
        shots = aws_quantum_task.metadata()["shots"]
        vendor_job_id = aws_quantum_task.metadata()["quantumTaskArn"]
        job_id = init_job(vendor_job_id, self, qbraid_circuit, shots)
        return BraketQuantumTaskWrapper(
            job_id, vendor_job_id=vendor_job_id, device=self, vendor_jlo=aws_quantum_task
        )
