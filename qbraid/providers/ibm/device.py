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
import re
from typing import TYPE_CHECKING, List, Union

from qiskit import transpile
from qiskit.transpiler import TranspilerError

from qbraid.programs.libs.qiskit import QiskitCircuit
from qbraid.providers.device import QuantumDevice
from qbraid.providers.enums import DeviceStatus, DeviceType

from .job import QiskitJob

if TYPE_CHECKING:
    import qiskit
    import qiskit_ibm_provider
    import qiskit_ibm_runtime


class QiskitBackend(QuantumDevice):
    """Wrapper class for IBM Qiskit ``Backend`` objects."""

    def __init__(
        self, ibm_device: Union["qiskit_ibm_provider.IBMBackend", "qiskit_ibm_runtime.IBMBackend"]
    ):
        """Create a QiskitBackend."""

        super().__init__(ibm_device)
        self._vendor = "IBM"
        self._run_package = "qiskit"

    def _get_device_name(self) -> str:
        """Get the name of the device."""
        backend = self._device
        if hasattr(backend, "backend_name"):
            return backend.backend_name

        if hasattr(backend, "name"):
            return backend.name() if callable(backend.name) else backend.name

        match = re.search(r"<\w+\('([^']+)'\)>", str(backend))
        return match.group(1) if match else str(backend)

    def _populate_metadata(
        self, device: Union["qiskit_ibm_provider.IBMBackend", "qiskit_ibm_runtime.IBMBackend"]
    ) -> None:
        """Populate device metadata using IBMBackend object."""
        # pylint: disable=attribute-defined-outside-init
        device_name = self._get_device_name()
        self._vendor_id = device_name
        self._name = device_name
        self._provider = "IBM"
        lower_device_name = device_name.lower()
        if lower_device_name.startswith("fake"):
            self._device_type = DeviceType.FAKE
        elif "simulator" in lower_device_name or "aer" in lower_device_name:
            self._device_type = DeviceType.SIMULATOR
        else:
            self._device_type = (
                DeviceType.SIMULATOR if getattr(device, "simulator", True) else DeviceType.QPU
            )

        try:
            if self._device_type == DeviceType.FAKE:
                self._num_qubits = getattr(device, "configuration", lambda: device)().n_qubits
            else:
                self._num_qubits = device.num_qubits
        except (AttributeError, TranspilerError):
            self._num_qubits = (
                5000
                if device.name == "simulator_stabilizer"
                else 63 if device.name == "simulator_extended_stabilizer" else None
            )

    def _transpile(self, run_input):
        if self._device_type.name != "FAKE" and self._device.local:
            program = QiskitCircuit(run_input)
            program.remove_idle_qubits()
            run_input = program.program

        return transpile(run_input, backend=self._device)

    def _compile(self, run_input):
        return run_input

    def status(self):
        """Return the status of this Device.

        Returns:
            str: The status of this Device
        """
        if self._device_type == DeviceType("FAKE"):
            return DeviceStatus.ONLINE

        backend_status = self._device.status()
        if not backend_status.operational or backend_status.status_msg != "active":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the ibm backend"""
        if self._device_type == DeviceType("FAKE"):
            return 0
        return self._device.status().pending_jobs

    def _run(
        self,
        run_input: "Union[qiskit.QuantumCircuit, List[qiskit.QuantumCircuit]]",
        *args,
        **kwargs,
    ):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.QuantumJob`
        object, applies a :class:`~qbraid.providers.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object to run on the IBM device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.QiskitJob: The job like object for the run.

        """
        backend = self._device
        shots = kwargs.pop("shots", backend.options.get("shots"))
        memory = kwargs.pop("memory", True)  # Needed to get measurements
        qiskit_job = backend.run(run_input, shots=shots, memory=memory)
        try:
            tags_lst = qiskit_job.update_tags(kwargs.get("tags", []))
        except AttributeError:  # BasicAerJob does not have update_tags
            tags_lst = []
        tags = {tag: "*" for tag in tags_lst}
        qiskit_job_id = qiskit_job.job_id()
        return {
            "vendor_job_id": qiskit_job_id,
            "tags": tags,
            "shots": shots,
            "vendor_job_obj": qiskit_job,
            "qbraid_job_obj": QiskitJob,
        }

    def _run_batch(self, run_input: "List[qiskit.QuantumCircuit]", *args, **kwargs):
        """Runs circuit(s) on qiskit backend via :meth:`~qiskit.execute`

        Uses the :meth:`~qiskit.execute` method to create a :class:`~qiskit.providers.QuantumJob`
        object, applies a :class:`~qbraid.providers.ibm.QiskitJob`, and return the result.

        Args:
            run_input: A circuit object list to run on the wrapped device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is 1024.

        Returns:
            qbraid.providers.ibm.QiskitJob: The job like object for the run.

        """
        return self._run(run_input, **kwargs)
