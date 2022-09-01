"""
Module defining QiskitSimulatorWrapper Class

"""
from qiskit import BasicAer
from qiskit import transpile as qiskit_transpile
from qiskit.providers import QiskitBackendNotFoundError

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .localjob import QiskitBasicAerJobWrapper


class QiskitBasicAerWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``LocalSimulator`` objects."""

    def _get_device(self):
        """Initialize an IBM simulator."""
        try:
            return BasicAer.get_backend(self._obj_arg)
        except QiskitBackendNotFoundError as err:
            raise DeviceError(f"Device not found.") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        return DeviceStatus.ONLINE

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.devices.ibm.QiskitJobWrapper`, and return the result.

        Args:
            run_input: An individual or a list of circuit objects to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.


        Returns:
            qbraid.devices.ibm.QiskitJobWrapper: The job like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        compiled_circuit = qiskit_transpile(run_input, self.vendor_dlo)
        qiskit_job = self.vendor_dlo.run(compiled_circuit, *args, **kwargs)
        return QiskitBasicAerJobWrapper(self, qiskit_job)

    def estimate_cost(self, circuit, shots=1024):
        """Estimate the cost of running a circuit on the device."""
        return 0.0
