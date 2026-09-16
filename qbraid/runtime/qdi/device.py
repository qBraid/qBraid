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
Module defining the QDI device class

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbraid.programs.typer import get_qasm_type_alias
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .exceptions import QdiDeviceError, qdi_call
from .job import QdiJob
from .protocol import QdiDeviceDescriptor

if TYPE_CHECKING:
    import qbraid.runtime
    from qbraid.runtime.qdi.protocol import QdiClient

# qBraid program alias -> QDI task types that carry it, most canonical first.
_TASK_TYPES_BY_ALIAS: dict[str, tuple[str, ...]] = {
    "qasm3": ("openqasm3", "qasm3"),
    "qasm2": ("openqasm2", "qasm2"),
}


class QdiDevice(QuantumDevice):
    """Quantum device driven through the QDI client surface."""

    def __init__(self, profile: qbraid.runtime.TargetProfile, client: QdiClient):
        super().__init__(profile=profile)
        self._client = client

    @property
    def client(self) -> QdiClient:
        """Return the QDI client this device submits through."""
        return self._client

    def __str__(self):
        return f"{self.__class__.__name__}('{self.id}')"

    def descriptor(self) -> QdiDeviceDescriptor | None:
        """Re-run Discover and return this device's current descriptor, or ``None`` if gone."""
        with qdi_call("discover"):
            response = self._client.discover()
        for entry in response["devices"]:
            if entry["device_id"] == self.id:
                return QdiDeviceDescriptor.from_dict(entry)
        return None

    def status(self) -> DeviceStatus:
        """Return ``ONLINE`` when the device reports ``is_ready``, ``UNAVAILABLE`` otherwise.

        QDI's readiness flag is the only status signal the spec defines. A
        device that no longer appears in Discover at all is ``OFFLINE``.
        """
        descriptor = self.descriptor()
        if descriptor is None:
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE if descriptor.is_ready else DeviceStatus.UNAVAILABLE

    def _task_type(self, program: str) -> str:
        """Pick the QDI ``task_type`` the device declared for this program's dialect."""
        alias = get_qasm_type_alias(program)
        declared = self.profile["supported_task_types"]
        for task_type in _TASK_TYPES_BY_ALIAS.get(alias, ()):
            if task_type in declared:
                return task_type
        raise QdiDeviceError(
            f"Device '{self.id}' declares task types {list(declared)}, none of which carry "
            f"'{alias}' programs."
        )

    def _check_extensions(self, extensions: dict[str, Any] | None) -> None:
        # Spec §3.2 has the device reject undeclared keys; checking here gives
        # a message naming the declared set before a round trip is spent.
        if not extensions:
            return
        declared = self.profile["supported_extensions"]
        unknown = sorted(set(extensions) - set(declared))
        if unknown:
            raise QdiDeviceError(
                f"Extension key(s) {unknown} are not declared by device '{self.id}'. "
                f"Supported extensions: {list(declared)}."
            )

    # The base signature is deliberately narrowed: QDI carries opaque bytes, and
    # after ``prepare`` the runtime hands this method OpenQASM text.
    # pylint:disable-next=arguments-differ
    def submit(  # type: ignore[override]
        self,
        run_input: str | list[str],
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> QdiJob | list[QdiJob]:
        """Send one or more OpenQASM programs to the device.

        Args:
            run_input: An OpenQASM 2/3 string, or a list of them (one QDI task each).
            shots: Execution shots per program.
            extensions: Vendor-specific parameters; every key must appear in the
                device's ``supported_extensions``.

        Returns:
            A :class:`~qbraid.runtime.qdi.QdiJob` per program.
        """
        is_single = isinstance(run_input, str)
        programs: list[str] = [run_input] if isinstance(run_input, str) else run_input
        self._check_extensions(extensions)

        jobs = []
        for program in programs:
            task_type = self._task_type(program)
            with qdi_call("send"):
                task_id = self._client.send(
                    self.id, program.encode("utf-8"), task_type, shots, extensions
                )
            jobs.append(
                QdiJob(task_id, client=self._client, device=self, shots=shots, task_type=task_type)
            )
        return jobs[0] if is_single else jobs

    def estimate(
        self,
        run_input: qbraid.programs.QPROGRAM,
        shots: int = 100,
        extensions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Dry-run a program through QDI Resource Estimation (spec §3.5).

        The program goes through the same transpile/validate/prepare pipeline
        as :meth:`run`, so any supported program type can be estimated.

        Raises:
            QdiDeviceError: If the device declares ``supports_estimation: false``.
        """
        if not self.profile["supports_estimation"]:
            raise QdiDeviceError(f"Device '{self.id}' does not support resource estimation.")
        self._check_extensions(extensions)
        program = self.apply_runtime_profile(run_input)
        if not isinstance(program, str):
            raise QdiDeviceError("Resource estimation takes a single program, not a batch.")
        task_type = self._task_type(program)
        with qdi_call("estimate_resources"):
            return self._client.estimate_resources(
                self.id, program.encode("utf-8"), task_type, shots, extensions
            )
