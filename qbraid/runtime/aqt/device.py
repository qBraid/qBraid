# Copyright 2026 qBraid
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
Module defining AQT device class.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aqt_connector.models.arnica.request_bodies.jobs import QuantumCircuits, SubmitJobRequest
from aqt_connector.models.arnica.resources import ResourceStatus

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import AQTJob

if TYPE_CHECKING:
    from aqt_connector.models.circuits import QuantumCircuit as AQTQuantumCircuit

    import qbraid.runtime
    import qbraid.runtime.aqt.provider

# Covers every member of arnica's ``ResourceStatus`` enum; a value outside it is rejected by
# ``ResourceDetails.model_validate`` before it reaches this map.
_STATUS_MAP = {
    ResourceStatus.ONLINE: DeviceStatus.ONLINE,
    ResourceStatus.OFFLINE: DeviceStatus.OFFLINE,
    ResourceStatus.MAINTENANCE: DeviceStatus.UNAVAILABLE,
    ResourceStatus.UNAVAILABLE: DeviceStatus.UNAVAILABLE,
}


class AQTDeviceError(QbraidRuntimeError):
    """Class for errors raised while processing an AQT device."""


class AQTDevice(QuantumDevice):
    """AQT quantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.aqt.provider.AQTSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.aqt.provider.AQTSession:
        """Return the AQT session."""
        return self._session

    def __str__(self):
        return f"{self.__class__.__name__}('{self.id}')"

    @property
    def workspace_id(self) -> str:
        """Return the arnica workspace id for this device."""
        return self.profile["aqt_workspace_id"]

    @property
    def resource_id(self) -> str:
        """Return the arnica resource id for this device."""
        return self.profile["aqt_resource_id"]

    def status(self) -> DeviceStatus:
        """Return the current status of the AQT device.

        Raises:
            AQTDeviceError: If arnica reports a resource status qBraid does not map yet.
        """
        details = self.session.get_resource(self.resource_id)
        try:
            return _STATUS_MAP[details.status]
        except KeyError as err:  # pragma: no cover - unreachable while _STATUS_MAP is exhaustive
            raise AQTDeviceError(f"Unrecognized AQT device status '{details.status}'.") from err

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: AQTQuantumCircuit | list[AQTQuantumCircuit],
        shots: int = 100,
        name: str | None = None,
    ) -> AQTJob:
        """Submit one or more AQT circuits to the device.

        Args:
            run_input: A native AQT ``QuantumCircuit`` (or a list of them for a batch), as produced
                by the ``qiskit -> aqt_connector`` transpiler conversion during ``run``. Each
                carries a placeholder ``repetitions`` that is overwritten with ``shots`` here.
            shots: Number of repetitions per circuit. Defaults to 100.
            name: Optional human-readable label for the job.

        Returns:
            AQTJob: A handle to the submitted job.
        """
        circuits = run_input if isinstance(run_input, list) else [run_input]
        request = SubmitJobRequest(
            label=name or "qbraid",
            payload=QuantumCircuits(
                circuits=[
                    # rebuild via type(circuit) to stamp the requested shots (re-validating ranges)
                    type(circuit)(
                        repetitions=shots,
                        quantum_circuit=circuit.quantum_circuit,
                        number_of_qubits=circuit.number_of_qubits,
                    )
                    for circuit in circuits
                ]
            ),
        )
        response = self.session.submit_job(
            self.workspace_id, self.resource_id, request.model_dump(mode="json")
        )
        # ``SubmitJobResponse`` requires ``job.job_id``, so a response missing it fails validation
        # in the session rather than producing an ``AQTJob`` with a bogus id.
        return AQTJob(
            job_id=str(response.job.job_id), session=self.session, device=self, shots=shots
        )
