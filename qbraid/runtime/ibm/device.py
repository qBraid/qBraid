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
from typing import TYPE_CHECKING, Optional, Union

from qiskit import transpile, QuantumCircuit

from qbraid.programs import ProgramSpec
from qbraid.programs.libs.qiskit import QiskitCircuit
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, DeviceType
from qbraid.runtime.profile import RuntimeProfile

from .job import QiskitJob

if TYPE_CHECKING:
    import qiskit
    import qiskit_ibm_runtime

    import qbraid.runtime.ibm


class QiskitBackend(QuantumDevice):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(
        self,
        name: Optional[str] = None,
        instance: Optional[str] = None,
        provider: "Optional[qbraid.runtime.ibm.QiskitRuntimeProvider]" = None,
        backend: "Optional[qiskit_ibm_runtime.IBMBackend]" = None,
    ):
        """Create a QiskitBackend."""
        if not (name or backend):
            raise ValueError("Must specify either name or backend.")
        if name and backend:
            raise ValueError("Can only specify one of name and backend.")
        super().__init__(device_id=name or backend.name, provider=provider)
        backend = backend or provider.runtime_service.backend(name, instance=instance)
        if backend.local:
            device_type = DeviceType.LOCAL_SIMULATOR
        elif backend.simulator:
            device_type = DeviceType.SIMULATOR
        else:
            device_type = DeviceType.QPU

        self._backend = backend
        self._device_type = device_type
        self._num_qubits = backend.configuration().n_qubits
        self._program_spec = ProgramSpec(QuantumCircuit)

    def _default_profile(self) -> "qbraid.runtime.RuntimeProfile":
        """Return the default runtime profile."""
        return RuntimeProfile(
            device_type=self._device_type,
            device_num_qubits=self._num_qubits,
            program_spec=self._program_spec,
        )

    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self == DeviceType.LOCAL_SIMULATOR:
            return DeviceStatus.ONLINE

        status = self._backend.status()
        if status.operational:
            if status.status_msg == "active":
                return DeviceStatus.ONLINE
            return DeviceStatus.UNAVAILABLE
        return DeviceStatus.OFFLINE

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the ibm backend"""
        if self.device_type == DeviceType.LOCAL_SIMULATOR:
            return 0
        return self._backend.status().pending_jobs

    def transform(self, run_input: "qiskit.QuantumCircuit") -> "qiskit.QuantumCircuit":
        if self.device_type == DeviceType.LOCAL_SIMULATOR:
            program = QiskitCircuit(run_input)
            program.remove_idle_qubits()
            run_input = program.program

        return transpile(run_input, backend=self._backend)

    def submit(
        self,
        run_input: "Union[qiskit.QuantumCircuit, list[qiskit.QuantumCircuit]]",
        *args,
        **kwargs,
    ) -> "qbraid.runtime.ibm.QiskitJob":
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.QuantumJob`
        object, applies a :class:`~qbraid.runtime.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object to run on the IBM device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.runtime.ibm.QiskitJob: The job like object for the run.

        """
        backend = self._backend
        shots = kwargs.pop("shots", backend.options.get("shots"))
        memory = kwargs.pop("memory", True)  # Needed to get measurements
        job = backend.run(run_input, *args, shots=shots, memory=memory, **kwargs)
        job_id = job.job_id()
        return QiskitJob(job_id, job=job, device=self)
