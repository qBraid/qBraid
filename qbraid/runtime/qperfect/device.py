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
Module defining QPerfect (MIMIQ) device class.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import QPerfectJob

if TYPE_CHECKING:
    from mimiqcircuits import Circuit as MimiqCircuit

    import qbraid.runtime
    import qbraid.runtime.qperfect.provider

# MIMIQ ``MimiqConnection.submit`` options that may be forwarded as runtime options. ``nsamples``
# (shots) and ``label`` (name) are set explicitly, so they are excluded here.
_SUBMIT_OPTIONS = frozenset(
    {
        "algorithm",
        "bitstrings",
        "timelimit",
        "bonddim",
        "entdim",
        "mpscutoff",
        "remove_swaps",
        "canonicaldecompose",
        "fuse",
        "reorderqubits",
        "reorderqubits_seed",
        "seed",
        "qasmincludes",
        "mpsmethod",
        "mpotraversal",
        "noisemodel",
        "streaming",
    }
)


class QPerfectDevice(QuantumDevice):
    """QPerfect (MIMIQ) simulator device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        provider: qbraid.runtime.qperfect.provider.QPerfectProvider,
    ):
        super().__init__(profile=profile)
        self._provider = provider

    def __str__(self):
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the device status based on connection health.

        MIMIQ exposes no device-status endpoint; the emulator is ``ONLINE`` when the provider can
        authenticate a connection to the cloud, and ``OFFLINE`` otherwise.
        """
        try:
            connection = self._provider.connection
            if connection.connection.isOpen():
                return DeviceStatus.ONLINE
            return DeviceStatus.OFFLINE
        except Exception:  # pylint: disable=broad-except
            return DeviceStatus.OFFLINE

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: MimiqCircuit | list[MimiqCircuit],
        shots: int = 100,
        *,
        name: str | None = None,
        **options: Any,
    ) -> QPerfectJob:
        """Submit one or more native MIMIQ circuits to the emulator.

        Args:
            run_input: A native ``mimiqcircuits.Circuit`` (or a list of them for a batch), as
                produced by the ``qiskit -> mimiqcircuits`` conversion during ``run``. A batch is
                executed as a single job; results come back per circuit in submission order.
            shots: Number of samples per circuit (MIMIQ ``nsamples``). Defaults to 100.
            name: Optional human-readable label for the job.
            **options: MIMIQ submit options forwarded to the emulator, e.g. ``algorithm``
                (``"auto"`` / ``"statevector"`` / ``"mps"``), ``timelimit``, ``bonddim``,
                ``entdim``, ``seed``, ``bitstrings``, or ``noisemodel``. ``algorithm`` defaults
                to ``"auto"`` for a single circuit, and is required for a batch.

        Returns:
            QPerfectJob: A handle to the submitted job.

        Raises:
            ValueError: If an unsupported submit option is passed, or if a batch is submitted
                without an explicit ``algorithm``.
        """
        unknown = set(options) - _SUBMIT_OPTIONS
        if unknown:
            raise ValueError(
                f"Unsupported MIMIQ submit option(s): {sorted(unknown)}. "
                f"Supported: {sorted(_SUBMIT_OPTIONS)}."
            )
        connection = self._provider.connection
        kwargs: dict[str, Any] = {"nsamples": shots, "label": name or "qbraid", **options}
        # MIMIQ rejects algorithm="auto" for batches, so only single circuits get the default.
        if not isinstance(run_input, list):
            kwargs.setdefault("algorithm", "auto")
        elif "algorithm" not in kwargs:
            raise ValueError(
                "Batch submission requires an explicit algorithm: pass algorithm='statevector' "
                "or algorithm='mps'. MIMIQ only supports algorithm='auto' for a single circuit."
            )
        execution = connection.submit(run_input, **kwargs)
        return QPerfectJob(job_id=str(execution), connection=connection, device=self, shots=shots)
