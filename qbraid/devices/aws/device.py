"""BraketDeviceWrapper Class"""
import math
import warnings

from braket.aws import AwsDevice

from qbraid.devices._utils import get_config, init_job, install
from qbraid.devices.aws.job import BraketQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, device_info):
        """Create a BraketDeviceWrapper."""

        super().__init__(device_info)
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
        # pylint: disable=import-outside-toplevel
        if self.provider != "D-Wave":
            raise DeviceError("Sampler only available for D-Wave (annealing) devices")
        try:
            from braket.ocean_plugin import BraketDWaveSampler, BraketSampler
        except ModuleNotFoundError:
            install("amazon-braket-ocean-plugin")
            from braket.ocean_plugin import BraketDWaveSampler, BraketSampler
        if braket_default:
            sampler = BraketSampler(self._s3_location, self._arn)
        else:
            sampler = BraketDWaveSampler(self._s3_location, self._arn)
        if embedding:
            try:
                from dwave.system.composites import EmbeddingComposite
            except ModuleNotFoundError:
                install("dwave-ocean-sdk")
                from dwave.system.composites import EmbeddingComposite
            return EmbeddingComposite(sampler)
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

    def estimate_cost(self, circuit, *args, shots=1024, **kwargs) -> float:
        """Estimate the cost of running a quantum task on this quantum device."""
        task_price = 0.3
        device = self._get_device()
        device_prop_dict = device.properties.dict()
        price = device_prop_dict["service"]["deviceCost"]["price"]
        estimate = 0
        # Simulators
        if device.name == "SV1" or device.name == "DM1":
            estimate = price * math.exp(shots / 1000)
        elif device.name == "TN1":
            estimate = price * circuit.num_qubits * math.exp(shots / 1000)
        # QPUs
        else:
            estimate = price * shots + task_price
        print("Your estimated cost is ${:.2f}".format(estimate))
        return estimate
