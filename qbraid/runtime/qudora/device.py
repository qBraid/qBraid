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

"""
Module defining QUDORA device class

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import QudoraJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.qudora.provider


# Maps QUDORA ``BackendStatusName`` values to qBraid ``DeviceStatus``.
_DEVICE_STATUS_MAP = {
    "Idle": DeviceStatus.ONLINE,
    "Executing": DeviceStatus.ONLINE,
    "Calibrating": DeviceStatus.UNAVAILABLE,
    "Unresponsive": DeviceStatus.OFFLINE,
}


class QudoraDevice(QuantumDevice):
    """QUDORA quantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.qudora.provider.QudoraSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.qudora.provider.QudoraSession:
        """Return the QUDORA session."""
        return self._session

    def __str__(self):
        """String representation of the QudoraDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the QUDORA device."""
        backend_id = self.profile.get("qudora_backend_id")
        if backend_id is None:
            # The QUDORA ``/backends/`` listing carries no per-backend status field, and the
            # status endpoint is keyed by an integer id. When that id is unavailable, a device
            # that appears in the listing is treated as online.
            return DeviceStatus.ONLINE
        status_name = self.session.get_backend_status(backend_id)
        return _DEVICE_STATUS_MAP.get(status_name, DeviceStatus.UNAVAILABLE)

    def available_settings(self) -> dict[str, Any]:
        """Return the configurable QUDORA backend settings and their schema.

        These are the keys accepted in ``backend_settings`` at submit time — for QUDORA's
        simulators, the noise parameters ``measurement_error_probability``,
        ``two_qubit_gate_noise_strength``, ``single_qubit_gate_noise_strength``, and
        ``dephasing_T2_time`` — each entry carrying its ``default`` (and any bounds). Derived
        from the backend's ``user_settings_schema``; empty when the backend exposes none.
        """
        schema = self.profile.get("user_settings_schema") or {}
        return schema.get("properties", {})

    @staticmethod
    def _detect_language(program: str) -> str:
        """Return the QUDORA ``language`` (``OpenQASM2``/``OpenQASM3``) for a QASM string."""
        for line in program.splitlines():
            stripped = line.strip()
            if stripped.startswith("OPENQASM"):
                if stripped.startswith("OPENQASM 2"):
                    return "OpenQASM2"
                if stripped.startswith("OPENQASM 3"):
                    return "OpenQASM3"
                break
        raise ValueError("Could not determine the OpenQASM version from the program header.")

    # pylint:disable-next=arguments-differ
    def submit(
        self,
        run_input: Union[str, list[str]],
        shots: int = 100,
        name: Optional[str] = None,
        backend_settings: Optional[dict[str, Any]] = None,
    ) -> QudoraJob:
        """Submit one or more OpenQASM programs to the QUDORA device.

        Args:
            run_input: An OpenQASM 2/3 string, or a list of them for a batch job.
            shots: Number of repetitions per program.
            name: Optional job name (defaults to ``"qbraid"``).
            backend_settings: Optional QUDORA backend settings (e.g. noise parameters).

        Returns:
            The submitted :class:`~qbraid.runtime.qudora.QudoraJob`.
        """
        programs = run_input if isinstance(run_input, list) else [run_input]

        max_programs = self.profile.get("max_programs_per_job")
        if max_programs is not None and len(programs) > max_programs:
            raise ValueError(
                f"Number of programs ({len(programs)}) exceeds the device's maximum of "
                f"{max_programs} programs per job."
            )

        languages = {self._detect_language(program) for program in programs}
        if len(languages) != 1:
            raise ValueError(
                "All programs in a single QUDORA job must use the same OpenQASM version."
            )

        body = {
            "name": name or "qbraid",
            "target": self.id,
            "language": languages.pop(),
            "shots": [shots] * len(programs),
            "input_data": programs,
            "backend_settings": backend_settings or {},
        }
        job_id = self.session.create_job(body)
        if job_id is None:
            raise ValueError("QUDORA job submission did not return a job id.")

        return QudoraJob(job_id=str(job_id), session=self.session, device=self, shots=shots)
