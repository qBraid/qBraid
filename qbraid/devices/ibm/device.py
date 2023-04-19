# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining IBMBackendWrapper Class

"""
from qiskit import transpile
from qiskit.providers import QiskitBackendNotFoundError
from qiskit.utils.quantum_instance import QuantumInstance
from qiskit_ibm_provider import IBMBackend, IBMProvider

from qbraid.api.job_api import init_job
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .job import IBMJobWrapper
from .result import IBMResultWrapper


class IBMBackendWrapper(DeviceLikeWrapper):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def _get_device(self) -> IBMBackend:
        """Initialize an IBM device."""
        try:
            provider = IBMProvider()
            return provider.get_backend(self.vendor_device_id)
        except QiskitBackendNotFoundError as err:
            raise DeviceError("Device not found.") from err

    def _vendor_compat_run_input(self, run_input):
        return transpile(run_input, self.vendor_dlo)

    @property
    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        backend_status = self.vendor_dlo.status()
        if not backend_status.operational or backend_status.status_msg != "active":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def pending_jobs(self):
        """Return the number of jobs in the queue for the ibm backend"""
        return self.vendor_dlo.status().pending_jobs

    def execute(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.utils.QuantumInstance.execute`.

        Creates a :class:`~qiskit.utils.QuantumInstance`, invokes its ``execute`` method,
        applies a IBMResultWrapper, and returns the result.

        Args:
            run_input: An individual or a list of circuit objects to run on the wrapped device.
            kwargs: Any kwarg options to pass to the device for the run.

        Returns:
            qbraid.devices.ibm.IBMResultWrapper: The result like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        quantum_instance = QuantumInstance(self.vendor_dlo, *args, **kwargs)
        qiskit_result = quantum_instance.execute(run_input)
        qbraid_result = IBMResultWrapper(qiskit_result)
        return qbraid_result

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.devices.ibm.IBMJobWrapper`, and return the result.

        Args:
            run_input: A circuit object to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.


        Returns:
            qbraid.devices.ibm.IBMJobWrapper: The job like object for the run.

        """
        backend = self.vendor_dlo
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        shots = backend.options.get("shots") if "shots" not in kwargs else kwargs.pop("shots")
        memory = (
            True if "memory" not in kwargs else kwargs.pop("memory")
        )  # Needed to get measurements
        transpiled = transpile(run_input, backend=backend)
        qiskit_job = backend.run(transpiled, shots=shots, memory=memory, **kwargs)
        qiskit_job_id = qiskit_job.job_id()
        qbraid_job_id = init_job(qiskit_job_id, self, qbraid_circuit, shots)
        qbraid_job = IBMJobWrapper(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_jlo=qiskit_job
        )
        return qbraid_job
