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
from typing import TYPE_CHECKING, Any

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import QuantinuumJob

if TYPE_CHECKING:
    from pytket.backends.backendinfo import BackendInfo

    from qbraid.runtime.profile import TargetProfile

logger = logging.getLogger(__name__)


class QuantinuumDeviceError(QbraidRuntimeError):
    """Exception raised by QuantinuumDevice."""


class QuantinuumDevice(QuantumDevice):
    """Quantinuum NEXUS device interface."""

    def __init__(
        self,
        profile: TargetProfile,
        backend_info: BackendInfo,
        **kwargs,
    ):
        super().__init__(profile=profile, **kwargs)
        self._backend_info = backend_info

    @property
    def backend_info(self) -> BackendInfo:
        """Return the pytket BackendInfo for this device."""
        return self._backend_info

    def __str__(self):
        """String representation of the QuantinuumDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the Quantinuum device."""
        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        # pylint: disable-next=import-outside-toplevel
        from qnexus.client.devices import DeviceStateEnum

        cfg = qnx.models.QuantinuumConfig(device_name=self.id)
        status = qnx.devices.status(cfg)
        if status in (DeviceStateEnum.ONLINE, DeviceStateEnum.RESERVED_ONLINE):
            return DeviceStatus.ONLINE
        if status in (DeviceStateEnum.MAINTENANCE, DeviceStateEnum.RESERVED_MAINTENANCE):
            return DeviceStatus.UNAVAILABLE
        return DeviceStatus.OFFLINE

    def transform(self, run_input):
        """Coerce input to a list of pytket ``Circuit`` objects."""
        # pylint: disable-next=import-outside-toplevel
        from pytket import Circuit

        if isinstance(run_input, (list, tuple)):
            return [item for c in run_input for item in self.transform(c)]
        if isinstance(run_input, Circuit):
            return [run_input]

        try:
            # pylint: disable=import-outside-toplevel
            from pytket.extensions.qiskit import qiskit_to_tk
            from qiskit import QuantumCircuit

            # pylint: enable=import-outside-toplevel

            if isinstance(run_input, QuantumCircuit):
                return [qiskit_to_tk(run_input)]
        except ImportError:
            pass

        raise TypeError(
            f"Unsupported run_input type {type(run_input)}; "
            "expected pytket.Circuit or qiskit.QuantumCircuit"
        )

    def run(self, run_input, *args, **kwargs):
        """Run a quantum program on this device.

        Overridden to avoid the base class iterating single pytket circuits
        as sequences; batching is handled inside :meth:`submit`.
        """
        return self.submit(run_input, *args, **kwargs)

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input,
        shots: int | None = None,
        **_: Any,
    ) -> QuantinuumJob:
        """Compile and submit a pytket circuit (or batch) to the Quantinuum device.

        NEXUS requires circuits to be uploaded, compiled, and then executed as
        separate job stages. This method blocks while waiting for the
        compilation step to finish, then returns a :class:`QuantinuumJob`
        referencing the asynchronous execution job.
        """
        # pylint: disable-next=import-outside-toplevel
        import qnexus as qnx

        # pylint: disable-next=import-outside-toplevel
        from qnexus.models.language import Language

        circuits_list = self.transform(run_input)

        project = qnx.projects.get_or_create(
            name=os.getenv("QUANTINUUM_NEXUS_PROJECT_NAME", "qbraid")
        )
        backend_config = qnx.QuantinuumConfig(device_name=self.id)

        def unique(label: str) -> str:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            return f"qbraid {label} {ts}-{uuid.uuid4().hex[:6]}"

        circuit_refs = [
            qnx.circuits.upload(name=unique(f"circuit-{i}"), circuit=c, project=project)
            for i, c in enumerate(circuits_list)
        ]

        opt = int(os.getenv("QUANTINUUM_NEXUS_OPT_LEVEL", "1"))
        compile_job = qnx.start_compile_job(
            programs=circuit_refs,
            name=unique("compile"),
            optimisation_level=opt,
            backend_config=backend_config,
            project=project,
        )
        # NOTE: blocking wait during dispatch; compilation time depends on queue and program size.
        logger.info(
            "Waiting for Quantinuum compilation job %s to complete...",
            getattr(compile_job, "id", getattr(compile_job, "job_id", str(compile_job))),
        )
        qnx.jobs.wait_for(compile_job)
        compiled_refs = [item.get_output() for item in qnx.jobs.results(compile_job)]

        nshots = int(shots or 1000)
        execute_job = qnx.start_execute_job(
            programs=compiled_refs,
            name=unique("execute"),
            n_shots=[nshots] * len(compiled_refs),
            backend_config=backend_config,
            project=project,
            language=Language.QIR,
        )
        job_id = (
            getattr(execute_job, "id", None)
            or getattr(execute_job, "job_id", None)
            or str(execute_job)
        )
        return QuantinuumJob(job_id=str(job_id), device=self, job=execute_job)
