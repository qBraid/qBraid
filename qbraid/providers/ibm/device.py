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
Module defining QiskitBackend Class

"""
from typing import TYPE_CHECKING  # pylint: disable=unused-import

from qiskit import transpile
from qiskit.transpiler import TranspilerError

from qbraid.providers.device import QuantumDevice
from qbraid.providers.enums import DeviceStatus, DeviceType

from .job import QiskitJob

if TYPE_CHECKING:
    import qiskit_ibm_provider


class QiskitBackend(QuantumDevice):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(self, ibm_device: "qiskit_ibm_provider.IBMBackend"):
        """Create a BraketDevice."""

        super().__init__(ibm_device)
        self._vendor = "IBM"
        self._run_package = "qiskit"

    def _populate_metadata(self, device: "qiskit_ibm_provider.IBMBackend") -> None:
        """Populate device metadata using IBMBackend object."""
        # pylint: disable=attribute-defined-outside-init
        self._id = device.name
        self._name = device.name
        self._provider = "IBM"
        self._device_type = DeviceType("SIMULATOR") if device.simulator else DeviceType("QPU")

        try:
            self._num_qubits = device.num_qubits
        except TranspilerError:
            if device.name == "simulator_stabilizer":
                self._num_qubits = 5000
            elif device.name == "simulator_extended_stabilizer":
                self._num_qubits = 63
            else:
                self._num_qubits = None

    def _transpile(self, run_input):
        return transpile(run_input, backend=self._device)

    def _compile(self, run_input):
        return run_input

    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        backend_status = self._device.status()
        if not backend_status.operational or backend_status.status_msg != "active":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the ibm backend"""
        return self._device.status().pending_jobs

    def run(self, run_input, *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.providers.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.QiskitJob: The job like object for the run.

        """
        backend = self._device
        qbraid_circuit = self.process_run_input(run_input)
        run_input = qbraid_circuit._program
        shots = backend.options.get("shots") if "shots" not in kwargs else kwargs.pop("shots")
        memory = (
            True if "memory" not in kwargs else kwargs.pop("memory")
        )  # Needed to get measurements
        qiskit_job = backend.run(run_input, shots=shots, memory=memory, **kwargs)
        qiskit_job_id = qiskit_job.job_id()
        qbraid_job_id = self._init_job(qiskit_job_id, [qbraid_circuit], shots)
        qbraid_job = QiskitJob(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_job_obj=qiskit_job
        )
        return qbraid_job

    def run_batch(self, run_input, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.Job` object,
        applies a :class:`~qbraid.providers.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object list to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.QiskitJob: The job like object for the run.

        """
        backend = self._device
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
        qbraid_job = QiskitJob(
            qbraid_job_id, vendor_job_id=qiskit_job_id, device=self, vendor_job_obj=qiskit_job
        )
        return qbraid_job
