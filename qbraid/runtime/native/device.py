# Copyright 2025 qBraid
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

# pylint: disable=arguments-differ,too-many-arguments

"""
Module defining QbraidDevice class

"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, overload

from qbraid_core.services.runtime import QuantumRuntimeClient
from qbraid_core.services.runtime.schemas import JobRequest, Program

from qbraid._logging import logger
from qbraid.programs import ExperimentType
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.group import get_active_group, get_active_group_session
from qbraid.runtime.noise import NoiseModel

from .calibrations import best_chain, edge_costs, qubit_costs
from .job import QbraidJob

if TYPE_CHECKING:
    import qbraid_core.services.runtime
    from qbraid_core.services.runtime.schemas import DeviceCalibration

    import qbraid.runtime


class QbraidDevice(QuantumDevice):
    """Class to represent a qBraid device."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        client: qbraid_core.services.runtime.QuantumRuntimeClient | None = None,
        **kwargs,
    ):
        """Create a new QbraidDevice object."""
        super().__init__(profile=profile, **kwargs)
        self._client = client or QuantumRuntimeClient()

    @property
    def client(self) -> QuantumRuntimeClient:
        """Return the QuantumClient object."""
        return self._client

    def __str__(self):
        """String representation of the QbraidDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return device status."""
        device_data = self.client.get_device(self.id)
        return device_data.status

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""
        device_data = self.client.get_device(self.id)
        return device_data.queueDepth or 0

    def get_calibrations(self) -> DeviceCalibration | None:
        """Return the latest calibration snapshot for this device.

        Fetched live on every call, so repeated calls track the platform's
        refresh cadence. The snapshot includes per-edge two-qubit gate errors
        (each entry naming the physical ``source``/``target`` qubit pair),
        per-qubit metrics, and calibration timestamps.

        Returns:
            The device's ``DeviceCalibration``, or ``None`` when the device
            has no published calibration data (e.g. simulators).
        """
        return self.client.get_device_calibrations(self.id)

    @cached_property
    def coupling_map(self) -> tuple[tuple[int, int], ...] | None:
        """Physical two-qubit connectivity, derived from calibration data.

        Every calibrated two-qubit gate edge names a physically coupled qubit
        pair, so the union of edges across all calibrated gates is the
        device's coupling graph. Cached per device instance — connectivity is
        fixed hardware topology; use :meth:`get_calibrations` for fresh error
        rates.

        Returns:
            Sorted ``(source, target)`` pairs, or ``None`` when the device has
            no published calibration data (e.g. simulators).
        """
        calibration = self.get_calibrations()
        if calibration is None:
            return None
        pairs = {
            (entry.source, entry.target)
            for gate_map in calibration.edges.values()
            for entries in gate_map.values()
            for entry in entries
        }
        return tuple(sorted(pairs))

    def best_qubits(self, num_qubits: int, gate: str | None = None) -> tuple[int, ...] | None:
        """Select the best-calibrated qubits for a circuit of ``num_qubits`` qubits.

        Fetches a fresh calibration snapshot and returns the connected chain of
        physical qubits maximizing estimated fidelity: the product of
        ``(1 - error)`` over each qubit's readout and gate errors and each
        edge's two-qubit gate error. The chain is returned in path order, ready
        for e.g. Qiskit's ``initial_layout``. Calibrations shift with every
        refresh, so select shortly before submitting.

        For devices that publish qubit metrics but no coupling edges (all-to-all
        connectivity, e.g. trapped ion), returns the ``num_qubits`` individually
        best-calibrated qubits instead of a chain.

        Args:
            num_qubits: Number of qubits the circuit needs.
            gate: Restrict edge errors to this two-qubit gate (e.g. ``"cz"``).
                By default each edge uses its best calibrated gate.

        Returns:
            Physical qubit ids, or ``None`` when the device has no published
            calibration data (e.g. simulators).

        Raises:
            ValueError: If the device is not gate-model (e.g. analog neutral
                atom, where atom geometry is programmable and there is no fixed
                qubit lattice to select from), ``num_qubits < 1``, no connected
                chain of that length exists, ``gate`` has no calibrated edges,
                or the device has fewer calibrated qubits than requested.
        """
        experiment_type = self.profile.experiment_type
        if experiment_type is not None and experiment_type != ExperimentType.GATE_MODEL:
            raise ValueError(
                "best_qubits applies to gate-model devices; this device's "
                f"experiment type is {experiment_type.name}"
            )
        if num_qubits < 1:
            raise ValueError(f"num_qubits must be a positive integer, got {num_qubits}")
        calibration = self.get_calibrations()
        if calibration is None:
            return None
        node_costs = qubit_costs(calibration)
        edge_costs_map = edge_costs(calibration, gate=gate)
        if num_qubits == 1 or not edge_costs_map:
            if len(node_costs) < num_qubits:
                raise ValueError(
                    f"Device has {len(node_costs)} calibrated qubits; {num_qubits} requested"
                )
            ranked = sorted(node_costs, key=lambda qubit: (node_costs[qubit], qubit))
            return tuple(ranked[:num_qubits])
        chain = best_chain(node_costs, edge_costs_map, num_qubits)
        if chain is None:
            raise ValueError(
                f"No connected chain of {num_qubits} qubits exists on this device's coupling graph"
            )
        return tuple(chain)

    def _resolve_noise_model(self, noise_model: NoiseModel | str) -> str:
        """Verify given noise model is supported by device and map to string representation."""
        if self.profile.noise_models is None:
            raise ValueError("Noise models are not supported by this device.")

        if isinstance(noise_model, NoiseModel):
            noise_model = noise_model.value
        elif not isinstance(noise_model, str):
            raise ValueError(
                f"Invalid type for noise model: {type(noise_model)}. Expected str or NoiseModel."
            )

        if noise_model not in self.profile.noise_models:
            raise ValueError(f"Noise model '{noise_model}' not supported by device.")

        return self.profile.noise_models.get(noise_model).name

    @overload
    def submit(
        self,
        run_input: Program,
        shots: int | None = None,
        name: str | None = None,
        tags: dict[str, str | int | bool] | None = None,
        runtime_options: dict[str, Any] | None = None,
        as_batch: bool = False,
    ) -> QbraidJob: ...

    @overload
    def submit(
        self,
        run_input: list[Program],
        shots: int | None = None,
        name: str | None = None,
        tags: dict[str, str | int | bool] | None = None,
        runtime_options: dict[str, Any] | None = None,
        as_batch: bool = False,
    ) -> list[QbraidJob]: ...

    @overload
    def submit(
        self,
        run_input: list[Program],
        shots: int | None = None,
        name: str | None = None,
        tags: dict[str, str | int | bool] | None = None,
        runtime_options: dict[str, Any] | None = None,
        as_batch: bool = True,
    ) -> QbraidJob: ...

    def submit(
        self,
        run_input: Program | list[Program],
        shots: int | None = None,
        name: str | None = None,
        tags: dict[str, str | int | bool] | None = None,
        runtime_options: dict[str, Any] | None = None,
        as_batch: bool = False,
    ) -> QbraidJob | list[QbraidJob]:
        """Submit a program to the device.

        If an active GroupJobSession context exists, the group QRN is
        automatically included in the job request and submitted jobs
        are registered with the session.

        Args:
            run_input: A single program or a list of programs to submit to the device.
            shots: The number of shots to run the program(s).
            name: The name of the job.
            tags: A dictionary of tags to add to the job.
            runtime_options: A dictionary of runtime options to pass to the device.
            as_batch: When True, submit all programs as a single batch job
                (one API call, one QRN, one status). Returns a single QbraidJob.
                Check QbraidDevice.profile.batch_job_support to verify if
                batch jobs are supported by this device.
        """
        tags = tags or {}
        runtime_options = runtime_options or {}
        noise_model: NoiseModel | str | None = runtime_options.pop("noise_model", None)

        # Read group context
        group_job_qrn = get_active_group()
        session = get_active_group_session() if group_job_qrn else None

        if noise_model:
            runtime_options["noiseModel"] = self._resolve_noise_model(noise_model)

        if as_batch:
            if not self.profile.get("batch_job_support"):
                raise ValueError("Batch jobs are not supported by this device.")

            if not isinstance(run_input, list):
                raise ValueError("Batch jobs require a list of programs.")

        # Wrap so the loop iterates once: [Program] for single, [list[Program]]
        # for batch (sends the full list as one API call → 1 QRN, N circuits).
        is_single_input = as_batch or not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input

        logger.debug(
            "Submitting %s to device '%s' (group: %s)",
            "batch job" if as_batch else f"{len(run_input)} job(s)",
            self.id,
            group_job_qrn,
        )

        jobs = []

        for program in run_input:
            job_request = JobRequest(
                deviceQrn=self.id,
                program=program,
                shots=shots,
                name=name,
                tags=tags,
                runtimeOptions=runtime_options,
                groupJobQrn=group_job_qrn,
            )
            job_data = self.client.create_job(job_request)
            job = QbraidJob(job_id=job_data.jobQrn, device=self, client=self.client)
            jobs.append(job)
            if session is not None:
                session._register_job(job)

        return jobs[0] if is_single_input else jobs
