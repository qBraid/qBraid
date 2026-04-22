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
Module defining Quantinuum device class.

"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import QuantinuumJob

if TYPE_CHECKING:
    from pytket.circuit import Circuit

    from qbraid.runtime.profile import TargetProfile

logger = logging.getLogger(__name__)


class QuantinuumDeviceError(QbraidRuntimeError):
    """Exception raised by QuantinuumDevice."""


class QuantinuumDevice(QuantumDevice):
    """Quantinuum NEXUS device interface."""

    def __init__(self, profile: TargetProfile, **kwargs):
        super().__init__(profile=profile, **kwargs)

    @property
    def backend_info(self):
        """Return the pytket BackendInfo for this device (from the profile)."""
        return self.profile.backend_info

    def __str__(self):
        """String representation of the QuantinuumDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the Quantinuum device."""
        # pylint: disable=import-outside-toplevel
        import qnexus as qnx
        from qnexus.client.devices import DeviceStateEnum

        # pylint: enable=import-outside-toplevel

        cfg = qnx.models.QuantinuumConfig(device_name=self.id)
        status = qnx.devices.status(cfg)
        if status in (DeviceStateEnum.ONLINE, DeviceStateEnum.RESERVED_ONLINE):
            return DeviceStatus.ONLINE
        if status in (DeviceStateEnum.MAINTENANCE, DeviceStateEnum.RESERVED_MAINTENANCE):
            return DeviceStatus.UNAVAILABLE
        return DeviceStatus.OFFLINE

    def submit(  # pylint: disable=arguments-differ
        self,
        run_input: Circuit | list[Circuit],
        shots: int = 1000,
        project_name: str | None = None,
        optimisation_level: int | None = None,
    ) -> QuantinuumJob:
        """Compile and submit a pytket circuit (or batch) to the Quantinuum device.

        NEXUS requires circuits to be uploaded, compiled, and then executed as
        separate job stages. This method blocks while waiting for the
        compilation step to finish, then returns a :class:`QuantinuumJob`
        referencing the asynchronous execution job.

        The ``run_input`` is assumed to already be in pytket ``Circuit`` form;
        the qBraid transpiler pipeline (invoked via the base class ``run``)
        handles any upstream format conversions based on the device's
        :class:`TargetProfile`.

        Args:
            run_input: pytket ``Circuit`` or a list thereof to execute.
            shots: Number of shots per circuit. Defaults to 1000.
            project_name: NEXUS project name to scope the compile and execute
                jobs under. Falls back to the ``QUANTINUUM_NEXUS_PROJECT_NAME``
                environment variable, and ultimately to ``"qbraid"``.
            optimisation_level: pytket optimisation level (0-2) passed to the
                NEXUS compile stage. Falls back to the
                ``QUANTINUUM_NEXUS_OPT_LEVEL`` environment variable, and
                ultimately to ``1``.
        """
        # pylint: disable=import-outside-toplevel
        import qnexus as qnx
        from qnexus.models.language import Language

        # pylint: enable=import-outside-toplevel

        circuits = run_input if isinstance(run_input, list) else [run_input]

        resolved_project_name = (
            project_name
            if project_name is not None
            else os.getenv("QUANTINUUM_NEXUS_PROJECT_NAME", "qbraid")
        )
        resolved_opt_level = (
            optimisation_level
            if optimisation_level is not None
            else int(os.getenv("QUANTINUUM_NEXUS_OPT_LEVEL", "1"))
        )

        project = qnx.projects.get_or_create(name=resolved_project_name)
        backend_config = qnx.QuantinuumConfig(device_name=self.id)

        def unique(label: str) -> str:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            return f"qbraid {label} {ts}-{uuid.uuid4().hex[:6]}"

        circuit_refs = [
            qnx.circuits.upload(name=unique(f"circuit-{i}"), circuit=c, project=project)
            for i, c in enumerate(circuits)
        ]

        compile_job = qnx.start_compile_job(
            programs=circuit_refs,
            name=unique("compile"),
            optimisation_level=resolved_opt_level,
            backend_config=backend_config,
            project=project,
        )
        # NOTE: blocking wait during dispatch; compilation time depends on queue and program size.
        logger.info("Waiting for Quantinuum compilation job %s to complete...", compile_job.id)
        qnx.jobs.wait_for(compile_job)
        compiled_refs = [item.get_output() for item in qnx.jobs.results(compile_job)]

        execute_job = qnx.start_execute_job(
            programs=compiled_refs,
            name=unique("execute"),
            n_shots=[shots] * len(compiled_refs),
            backend_config=backend_config,
            project=project,
            language=Language.QIR,
        )
        return QuantinuumJob(job_id=str(execute_job.id), device=self, job=execute_job)
