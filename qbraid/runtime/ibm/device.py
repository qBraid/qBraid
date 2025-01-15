# Copyright (C) 2024 qBraid
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
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qiskit.transpiler import PassManager
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime import SamplerV2 as Sampler

from qbraid.programs import load_program
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.options import RuntimeOptions

from .job import QiskitJob

if TYPE_CHECKING:
    import qiskit
    import qiskit_ibm_runtime

    import qbraid.runtime.ibm


class QiskitBackend(QuantumDevice):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        service: Optional[qiskit_ibm_runtime.QiskitRuntimeService] = None,
    ):
        """Create a QiskitBackend."""
        options = RuntimeOptions(pass_manager=None)
        options.set_validator("pass_manager", lambda x: x is None or isinstance(x, PassManager))

        super().__init__(profile=profile, options=options)
        self._service = service or QiskitRuntimeService()
        self._backend = self._service.backend(
            self.id, instance=getattr(self.profile, "instance", None)
        )

    def __str__(self):
        """String representation of the QiskitBackend object."""
        return f"{self.__class__.__name__}('{self._backend.name}')"

    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if getattr(self.profile, "local", False):
            return DeviceStatus.ONLINE

        status = self._backend.status()
        if status.operational:
            if status.status_msg == "active":
                return DeviceStatus.ONLINE
            return DeviceStatus.UNAVAILABLE
        return DeviceStatus.OFFLINE

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the ibm backend"""
        if getattr(self.profile, "local", False):
            return 0
        return self._backend.status().pending_jobs

    def transform(self, run_input: qiskit.QuantumCircuit) -> qiskit.QuantumCircuit:
        """Transpile a circuit for the device."""
        program = load_program(run_input)
        program.transform(self)
        return program.program

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: qiskit.QuantumCircuit | list[qiskit.QuantumCircuit],
        shots: int | None = None,
    ) -> qbraid.runtime.ibm.QiskitJob:
        """Runs circuit(s) on qiskit backend via :meth:`~SamplerV2.run`.

        Uses the :meth:`SamplerV2.execute` method to create a
        :class:`~qbraid.runtime.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object to run on the IBM device.
            shots (int, optional): The number of times to run the task on the device. If None,
                number of shots is determined by the sampler.

        Keyword Args:
            shots (int, optional): The number of times to run the task on the device. If None,
                number of shots is determined by the sampler.

        Returns:
            qbraid.runtime.ibm.QiskitJob: The job like object for the run.

        """
        backend = self._backend
        sampler = Sampler(mode=backend)
        pubs = run_input if isinstance(run_input, list) else [run_input]
        job = sampler.run(pubs, shots=shots)
        return QiskitJob(job.job_id(), job=job, device=self)
