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
Module defining QbraidJob class

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type, Union

from qbraid_core.services.quantum import QuantumClient

from qbraid._logging import logger
from qbraid.programs import ExperimentType
from qbraid.runtime.enums import JobStatus
from qbraid.runtime.exceptions import JobStateError, QbraidRuntimeError
from qbraid.runtime.job import QuantumJob
from qbraid.runtime.result import Result, ResultDataType
from qbraid.runtime.result_data import AhsResultData, AnnealingResultData, GateModelResultData
from qbraid.runtime.schemas import RuntimeJobModel

from .result import (
    NECVectorAnnealerResultData,
    QbraidQirSimulatorResultData,
    QuEraQasmSimulatorResultData,
)

if TYPE_CHECKING:
    import qbraid_core.services.quantum

    import qbraid.runtime


class QbraidJob(QuantumJob):
    """Class representing a qBraid job."""

    def __init__(
        self,
        job_id: str,
        device: Optional[qbraid.runtime.QbraidDevice] = None,
        client: Optional[qbraid_core.services.quantum.QuantumClient] = None,
        **kwargs,
    ):
        super().__init__(job_id, device, **kwargs)
        self._client = client

    @property
    def client(self) -> qbraid_core.services.quantum.QuantumClient:
        """
        Lazily initializes and returns the client object associated with the job.
        If the job has an associated device with a client, that client is used.
        Otherwise, a new instance of QuantumClient is created and used.

        Returns:
            QuantumClient: The client object associated with the job.
        """
        if self._client is None:
            self._client = self._device.client if self._device else QuantumClient()
        return self._client

    def queue_position(self) -> Optional[int]:
        """Return the position of the job in the queue."""
        job_data = self.metadata()
        return job_data.get("queue_position", job_data.get("queuePosition"))

    def status(self) -> JobStatus:
        """Return the status of the job / task , among the values of ``JobStatus``."""
        terminal_states = JobStatus.terminal_states()
        if self._cache_metadata.get("status") not in terminal_states:
            client_data = self.client.get_job(self.id)
            job_model = RuntimeJobModel.from_dict(client_data)
            job_data = job_model.model_dump(exclude={"metadata", "cost"})
            status = JobStatus(job_data.pop("status"))
            if job_model.status_text is not None:
                status.set_status_message(job_model.status_text)
            self._cache_metadata.update({**job_data, "status": status})
        return self._cache_metadata["status"]

    def cancel(self) -> None:
        """Attempt to cancel the job."""
        if self.is_terminal_state():
            raise JobStateError("Cannot cancel job in a terminal state.")

        self.client.cancel_job(self.id)
        logger.info("Cancel job request validated.")

        try:
            logger.info("Waiting for job to cancel...")
            self.wait_for_final_state(timeout=3, poll_interval=1)
        except TimeoutError:
            pass

        status = self.status()
        if status not in {JobStatus.CANCELLED, JobStatus.CANCELLING}:
            raise QbraidRuntimeError(f"Failed to cancel job. Current status: {status.name}")

        logger.info("Success. Current status: %s", status.name)

    @staticmethod
    def get_result_data_cls(
        device_id: Optional[str] = None, experiment_type: Optional[ExperimentType] = None
    ) -> Union[Type[GateModelResultData], Type[AnnealingResultData], Type[AhsResultData]]:
        """Determine the appropriate ResultData class based on device_id and experiment_type."""
        device_to_result_data = {
            "qbraid_qir_simulator": QbraidQirSimulatorResultData,
            "quera_qasm_simulator": QuEraQasmSimulatorResultData,
            "nec_vector_annealer": NECVectorAnnealerResultData,
        }

        result_data_cls = device_to_result_data.get(device_id)

        if not result_data_cls:
            experiment_type_to_result_data = {
                ExperimentType.GATE_MODEL: GateModelResultData,
                ExperimentType.ANNEALING: AnnealingResultData,
                ExperimentType.AHS: AhsResultData,
            }
            result_data_cls = experiment_type_to_result_data.get(experiment_type)

        if not result_data_cls:
            raise ValueError(
                f"Unsupported device_id '{device_id}' or experiment_type '{experiment_type.name}'"
            )

        return result_data_cls

    def result(self, timeout: Optional[int] = None) -> Result[ResultDataType]:
        """Return the results of the job."""
        self.wait_for_final_state(timeout=timeout)
        job_data = self.client.get_job(self.id)
        success = job_data.get("status") == JobStatus.COMPLETED.name
        job_result = (
            self.client.get_job_results(self.id, wait_time=1, backoff_factor=1.4) if success else {}
        )
        job_result.update(job_data)
        model = RuntimeJobModel.from_dict(job_result)
        result_data_cls = self.get_result_data_cls(model.device_id, model.experiment_type)
        data = result_data_cls.from_object(model.metadata)
        exclude = (
            {"solutions", "num_solutions"}
            if model.experiment_type == ExperimentType.ANNEALING
            else {"measurement_counts", "measurements"}
        )
        metadata_dump = model.metadata.model_dump(by_alias=True, exclude=exclude)
        model_dump = model.model_dump(
            by_alias=True, exclude={"job_id", "device_id", "metadata", "queue_position"}
        )
        experiment_type: ExperimentType = model_dump["experimentType"]
        status_text = (
            model.status_text or model.status.status_message or model.status.default_message
        )
        model_dump.update(
            {
                "status": model.status.name,
                "statusText": status_text,
                "experimentType": experiment_type,
            }
        )
        model_dump["metadata"] = metadata_dump
        return Result[ResultDataType](
            device_id=model.device_id, job_id=model.job_id, success=success, data=data, **model_dump
        )
