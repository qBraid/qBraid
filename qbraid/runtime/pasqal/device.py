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
Module defining Pasqal device class.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import PasqalJob

if TYPE_CHECKING:
    from pasqal_cloud import SDK as PasqalSDK

    from qbraid.runtime.profile import TargetProfile


class PasqalDeviceError(QbraidRuntimeError):
    """Exception raised by :class:`PasqalDevice`."""


class PasqalDevice(QuantumDevice):
    """Pasqal Cloud Services device interface.

    Wraps a Pasqal device identifier (QPU or emulator) and submits
    serialized Pulser sequences as Pasqal Cloud batches.
    """

    def __init__(self, profile: TargetProfile, sdk: PasqalSDK, **kwargs):
        """Initialize the Pasqal device.

        Args:
            profile: The :class:`TargetProfile` describing this device.
            sdk: Authenticated ``pasqal_cloud.SDK`` instance used to talk to
                the Pasqal Cloud Services API.
            **kwargs: Forwarded to :class:`QuantumDevice`.
        """
        super().__init__(profile=profile, **kwargs)
        self._sdk = sdk

    @property
    def sdk(self) -> PasqalSDK:
        """Return the underlying ``pasqal_cloud.SDK`` instance."""
        return self._sdk

    def __str__(self):
        """String representation of the :class:`PasqalDevice`."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """Return the current status of the Pasqal device.

        Pasqal Cloud Services does not expose a stable per-device status
        endpoint outside of the batch lifecycle. We surface ``ONLINE`` when
        the device identifier resolves and rely on per-batch error handling
        downstream.
        """
        return DeviceStatus.ONLINE

    def submit(  # pylint: disable=arguments-differ
        self,
        run_input: str | list[str],
        shots: int = 100,
        wait: bool = False,
    ) -> PasqalJob:
        """Submit a Pulser sequence (or batch of them) to the Pasqal device.

        The sequence(s) are serialized via Pulser's abstract representation,
        wrapped in a Pasqal Cloud *batch*, and submitted under the device
        identifier carried on this device's :class:`TargetProfile`.

        When a list is provided, all sequences share the batch but are sent
        as separate jobs, each with its own ``serialized_sequence``. The
        returned :class:`PasqalJob` is keyed by the underlying Pasqal batch
        id; per-job results are aggregated on retrieval.

        Args:
            run_input: A pre-serialized Pulser abstract-repr string (or list
                thereof). Serialization is handled upstream by the qBraid
                runtime via ``ProgramSpec.serialize`` before this method
                is called.
            shots: Number of repetitions per sequence. Defaults to 100.
            wait: When ``True``, block until the underlying batch reaches a
                terminal state before returning. Defaults to ``False``.

        Returns:
            A :class:`PasqalJob` referencing the submitted Pasqal Cloud batch.
        """
        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud.device import DeviceTypeName

        sequences = run_input if isinstance(run_input, list) else [run_input]

        if shots <= 0:
            raise PasqalDeviceError(f"`shots` must be a positive integer, got {shots}.")

        if not sequences:
            raise PasqalDeviceError("submit() requires at least one Pulser sequence.")

        # Pasqal accepts a batch-level sequence with per-job variables OR
        # per-job sequences with no batch-level sequence. We use the
        # per-job-sequence layout so heterogeneous sequences are supported
        # without requiring callers to parameterise. Per the pasqal-cloud
        # README: when a batch has no batch-level sequence, all jobs must
        # carry their own ``serialized_sequence``.
        jobs = [{"runs": shots, "serialized_sequence": seq} for seq in sequences]

        device_type = self._resolve_device_type(DeviceTypeName)

        try:
            batch = self._sdk.create_batch(
                jobs=jobs,
                device_type=device_type,
                wait=wait,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise PasqalDeviceError(
                f"Failed to submit batch to Pasqal device '{self.id}': {exc}"
            ) from exc

        return PasqalJob(job_id=batch.id, sdk=self._sdk, device=self)

    def _resolve_device_type(self, device_type_enum):
        """Map this device's id to a ``pasqal_cloud.DeviceTypeName`` member.

        Args:
            device_type_enum: The ``pasqal_cloud.device.DeviceTypeName`` enum
                class. Passed in to keep the (heavy) import out of module
                load time.

        Raises:
            PasqalDeviceError: If the device id does not correspond to a
                known Pasqal device type.
        """
        normalized = str(self.id).strip().upper()
        try:
            return device_type_enum(normalized)
        except ValueError as exc:
            raise PasqalDeviceError(
                f"Unknown Pasqal device type '{self.id}'. "
                f"Expected one of: {[m.value for m in device_type_enum]}."
            ) from exc
