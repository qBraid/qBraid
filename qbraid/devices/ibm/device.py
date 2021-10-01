"""QiskitBackendWrapper Class"""

from qiskit import IBMQ, Aer, BasicAer, execute
from qiskit.providers.backend import Backend as QiskitBackend
from qiskit.providers.ibmq import least_busy, IBMQProviderError
from qiskit.utils.quantum_instance import QuantumInstance

from qbraid.devices._utils import get_config
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.exceptions import DeviceError
from qbraid.devices.ibm.job import QiskitJobWrapper
from qbraid.devices.ibm.result import QiskitResultWrapper


class QiskitBackendWrapper(DeviceLikeWrapper):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(self, device_info, **kwargs):
        """Create a QiskitBackendWrapper."""

        super().__init__(device_info, **kwargs)

    def _get_device(self, obj_ref, obj_arg) -> QiskitBackend:
        """Initialize an IBM device."""
        if obj_ref == "IBMQ":
            if IBMQ.active_account() is None:
                IBMQ.load_account()
            group = get_config("group", "IBM")
            project = get_config("project", "IBM")
            try:
                provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
            except IBMQProviderError:
                IBMQ.load_account()
                provider = IBMQ.get_provider(hub="ibm-q", group=group, project=project)
            if obj_arg == "least_busy":
                backends = provider.backends(filters=lambda x: not x.configuration().simulator)
                return least_busy(backends)
            else:
                return provider.get_backend(obj_arg)
        elif obj_ref == "Aer":
            return Aer.get_backend(obj_arg)
        elif obj_ref == "BasicAer":
            return BasicAer.get_backend(obj_arg)
        else:
            raise DeviceError(f"obj_ref {obj_ref} not found.")

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self._obj_ref == "IBMQ":
            backend_status = self.vendor_dlo.status()
            if not backend_status.operational:
                return "OFFLINE"
        return "ONLINE"

    def execute(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.utils.QuantumInstance.execute`.

        Creates a :class:`~qiskit.utils.QuantumInstance`, invokes its ``execute`` method,
        applies a QiskitResultWrapper, and returns the result.

        Args:
            run_input: An individual or a list of circuit objects to run on the wrapped device.
            kwargs: Any kwarg options to pass to the device for the run.

        Returns:
            qbraid.devices.ibm.QiskitResultWrapper: The result like object for the run.

        """
        run_input = self._compat_run_input(run_input)
        quantum_instance = QuantumInstance(self.vendor_dlo, *args, **kwargs)
        qiskit_result = quantum_instance.execute(run_input)
        qbraid_result = QiskitResultWrapper(qiskit_result)
        return qbraid_result

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.devices.ibm.QiskitJobWrapper`, and return the result.

        Args:
            run_input: An individual or a list of circuit objects to run on the wrapped device.

        Keyword Args:
            shots (int): shots (int): The number of times to run the task on the device.
            Default is 1024.


        Returns:
            qbraid.devices.ibm.QiskitJobWrapper: The job like object for the run.

        """
        run_input = self._compat_run_input(run_input)
        qiskit_device = self.vendor_dlo
        qiskit_job = execute(run_input, qiskit_device, *args, **kwargs)
        qbraid_job = QiskitJobWrapper(self, qiskit_job)
        return qbraid_job
