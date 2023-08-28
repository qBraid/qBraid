# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining IBMBackendWrapper Class

"""
from qiskit import transpile
from qiskit.providers import QiskitBackendNotFoundError
from qiskit_ibm_provider import IBMBackend, IBMProvider

from qbraid.providers.device import DeviceLikeWrapper
from qbraid.providers.enums import DeviceStatus
from qbraid.providers.exceptions import DeviceError

from .job import IBMJobWrapper


class IBMBackendWrapper(DeviceLikeWrapper):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def _get_device(self) -> IBMBackend:
        """Initialize an IBM device."""
        try:
            provider = IBMProvider()
            return provider.get_backend(self.vendor_device_id)
        except QiskitBackendNotFoundError as err:
            raise DeviceError("Device not found.") from err

    def _transpile(self, run_input):
        return transpile(run_input, backend=self.vendor_dlo)

    def _compile(self, run_input):
        return run_input

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

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.providers.ibm.IBMJobWrapper`, and return the result.

        Args:
            run_input: A circuit object to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.IBMJobWrapper: The job like object for the run.

        """
        backend = self.vendor_dlo
        qbraid_circuit = self.process_run_input(run_input)
        run_input = qbraid_circuit._program
        shots = backend.options.get("shots") if "shots" not in kwargs else kwargs.pop("shots")
        memory = (
            True if "memory" not in kwargs else kwargs.pop("memory")
        )  # Needed to get measurements
        qiskit_job = backend.run(run_input, shots=shots, memory=memory, **kwargs)
        qiskit_job_id = qiskit_job.job_id()
        qbraid_job_id = self._init_job(qiskit_job_id, [qbraid_circuit], shots)
        qbraid_job = IBMJobWrapper(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_jlo=qiskit_job
        )
        return qbraid_job

    def run_batch(self, run_input, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.providers.ibm.IBMJobWrapper`, and return the result.

        Args:
            run_input: A circuit object list to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.IBMJobWrapper: The job like object for the run.

        """
        backend = self.vendor_dlo
        qbraid_circuit_batch = []
        run_input_batch = []
        for circuit in run_input:
            qbraid_circuit = self.process_run_input(circuit)
            run_input = qbraid_circuit._program
            run_input_batch.append(run_input)
            qbraid_circuit_batch.append(qbraid_circuit)

        shots = backend.options.get("shots") if "shots" not in kwargs else kwargs.pop("shots")
        memory = (
            True if "memory" not in kwargs else kwargs.pop("memory")
        )  # Needed to get measurements
        qiskit_job = backend.run(run_input_batch, shots=shots, memory=memory, **kwargs)
        qiskit_job_id = qiskit_job.job_id()

        # to change to batch
        qbraid_job_id = self._init_job(qiskit_job_id, qbraid_circuit_batch, shots)
        qbraid_job = IBMJobWrapper(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_jlo=qiskit_job
        )
        return qbraid_job
