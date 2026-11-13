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

import json
from typing import TYPE_CHECKING, Any, Union

from qbraid._logging import logger
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, ValidationLevel
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import PasqalJob, _pasqal_cloud_errors

if TYPE_CHECKING:
    from pasqal_cloud import SDK
    from pasqal_cloud.pasqal_cloud_client import PasqalCloudClient
    from pulser.backend import EmulationConfig
    from typing_extensions import TypeAlias

    import qbraid.programs
    from qbraid.runtime.profile import TargetProfile

    from .provider import PasqalSession

    PasqalClient: TypeAlias = Union[PasqalCloudClient, SDK]


# Device ids already warned about as untargetable, so a refresh does not repeat it.
_WARNED_UNTARGETABLE: set[str] = set()


class PasqalDeviceError(QbraidRuntimeError):
    """Exception raised by :class:`PasqalDevice`."""


def _serialize_run_input(run_input: str | dict[str, Any]) -> str:
    """Return a Pulser abstract-representation JSON string for one sequence.

    Accepts the abstract-repr string :meth:`PasqalDevice.run` produces, and the
    ``{"sequence_builder": ...}`` payload the qBraid platform stores for
    ``pulser.sequence`` programs (the same shape Azure Quantum expects), as a dict
    or as JSON text, which is how the CLI uploads a file.

    Raises:
        PasqalDeviceError: If the payload is neither form.
    """
    if isinstance(run_input, str):
        try:
            parsed = json.loads(run_input)
        except ValueError:
            return run_input
        if not (isinstance(parsed, dict) and "sequence_builder" in parsed):
            return run_input
        run_input = parsed
    if isinstance(run_input, dict) and isinstance(run_input.get("sequence_builder"), (str, dict)):
        builder = run_input["sequence_builder"]
        return builder if isinstance(builder, str) else json.dumps(builder)
    raise PasqalDeviceError(
        "Expected a Pulser abstract-representation string or a "
        "{'sequence_builder': ...} payload, got "
        f"{type(run_input).__name__}."
    )


def _serialize_backend_configuration(
    config: EmulationConfig | str | dict[str, Any] | None,
) -> str | None:
    """Return the abstract-representation string Pasqal expects for ``backend_configuration``.

    Raises:
        PasqalDeviceError: If ``config`` is not an ``EmulationConfig``, a string or a dict.
    """
    if config is None or isinstance(config, str):
        return config
    if isinstance(config, dict):
        return json.dumps(config)
    to_abstract_repr = getattr(config, "to_abstract_repr", None)
    if callable(to_abstract_repr):
        return to_abstract_repr()
    raise PasqalDeviceError(
        "Expected `backend_configuration` to be a Pulser EmulationConfig or its abstract "
        f"representation (a JSON string or dict), got {type(config).__name__}."
    )


class PasqalDevice(QuantumDevice):
    """Pasqal Cloud Services device interface.

    Wraps a Pasqal device identifier (QPU or emulator) and submits
    serialized Pulser sequences as Pasqal Cloud batches.
    """

    def __init__(
        self, profile: TargetProfile, client: PasqalClient, session: PasqalSession, **kwargs
    ):
        """Initialize the Pasqal device.

        Args:
            profile: The :class:`TargetProfile` describing this device.
            client: Authenticated ``pasqal_cloud`` client used to submit and
                track batches.
            session: Session reading Pasqal's device catalog, for status.
            **kwargs: Forwarded to :class:`QuantumDevice`.
        """
        super().__init__(profile=profile, **kwargs)
        self._client = client
        self._session = session

    @property
    def client(self) -> PasqalClient:
        """Return the underlying ``pasqal_cloud`` client."""
        return self._client

    def __str__(self):
        """String representation of the :class:`PasqalDevice`."""
        return f"{self.__class__.__name__}('{self.id}')"

    def _catalog_record(self) -> dict[str, Any] | None:
        """Return this device's live catalog entry, or ``None`` when Pasqal does not list it."""
        return self._session.get_device_records().get(self.id)

    def validate(
        self,
        run_input_batch: list[qbraid.programs.QPROGRAM],
        suppress_device_warning: bool = False,
    ) -> None:
        """Validate run input; if the device catalog is unreachable, skip only the status check.

        Submission does not use the catalog, so :meth:`run` is not refused because the
        device's status cannot be read.
        """
        level = ValidationLevel(self._options.get("validate", 0))
        if level != ValidationLevel.NONE and not suppress_device_warning:
            # pylint: disable-next=import-outside-toplevel
            from .provider import PasqalProviderError

            try:
                self.status()
            except PasqalProviderError as exc:
                logger.warning("Skipping the Pasqal device status check: %s", exc)
                suppress_device_warning = True
        super().validate(run_input_batch, suppress_device_warning=suppress_device_warning)

    def status(self) -> DeviceStatus:
        """Return the device's live status from Pasqal's device catalog.

        Pasqal reports ``status: "UP"`` for a device taking jobs. A device type
        Pasqal accepts but does not list (for example a QPU in maintenance) is
        ``OFFLINE``. A listed device is ``UNAVAILABLE`` when it is not up,
        inactive or not ``ACTIVE``, when its record is incomplete, or when the
        installed ``pasqal-cloud`` cannot target it (it was listed before the
        library added it), since a submission would fail.
        """
        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud.device import DeviceTypeName

        record = self._catalog_record()
        if record is None:
            return DeviceStatus.OFFLINE
        if self.id not in {member.value for member in DeviceTypeName}:
            if self.id not in _WARNED_UNTARGETABLE:
                _WARNED_UNTARGETABLE.add(self.id)
                logger.warning(
                    "Pasqal lists %s, which the installed pasqal-cloud cannot submit to; "
                    "reporting UNAVAILABLE.",
                    self.id,
                )
            return DeviceStatus.UNAVAILABLE
        status, active, availability = (
            record.get("status"),
            record.get("active"),
            record.get("availability"),
        )
        if status == "UP" and active is True and availability == "ACTIVE":
            return DeviceStatus.ONLINE
        if status not in {"UP", "DOWN"}:
            logger.warning(
                "Unrecognized Pasqal device status %r for %s; reporting UNAVAILABLE.",
                status,
                self.id,
            )
        return DeviceStatus.UNAVAILABLE

    def submit(  # pylint: disable=arguments-differ
        self,
        run_input: str | dict[str, Any] | list[str | dict[str, Any]],
        shots: int = 100,
        wait: bool = False,
        tags: list[str] | None = None,
        backend_configuration: EmulationConfig | str | dict[str, Any] | None = None,
    ) -> PasqalJob:
        """Submit a Pulser sequence (or batch of them) to the Pasqal device.

        The sequence(s) are wrapped in a Pasqal Cloud *batch* and submitted
        under the device identifier carried on this device's
        :class:`TargetProfile`.

        When a list is provided, all sequences share the batch but are sent
        as separate jobs, each with its own ``serialized_sequence``. The
        returned :class:`PasqalJob` is keyed by the underlying Pasqal batch
        id; per-job results are aggregated on retrieval.

        Args:
            run_input: A Pulser abstract-repr string, a qBraid
                ``{"sequence_builder": ...}`` payload, or a list of either.
                :meth:`run` serializes Pulser ``Sequence`` objects into the
                string form before this method is called.
            shots: Number of repetitions per sequence. Defaults to 100.
            wait: When ``True``, block until the underlying batch reaches a
                terminal state before returning. Defaults to ``False``.
            tags: Optional tags recorded on the Pasqal batch, e.g. a job name.
            backend_configuration: Emulator settings, as a Pulser ``EmulationConfig``
                (e.g. ``RemoteMPSBackend.default_config.with_changes(max_bond_dim=100)``)
                or its abstract representation. Pasqal validates it and rejects the
                batch if it cannot read it. Defaults to the emulator's own settings.

        Returns:
            A :class:`PasqalJob` referencing the submitted Pasqal Cloud batch.
        """
        # pylint: disable-next=import-outside-toplevel
        from pasqal_cloud.device import DeviceTypeName

        inputs = run_input if isinstance(run_input, list) else [run_input]

        if shots <= 0:
            raise PasqalDeviceError(f"`shots` must be a positive integer, got {shots}.")

        if not inputs:
            raise PasqalDeviceError("submit() requires at least one Pulser sequence.")

        # Pasqal accepts a batch-level sequence with per-job variables OR
        # per-job sequences with no batch-level sequence. We use the
        # per-job-sequence layout so heterogeneous sequences are supported
        # without requiring callers to parameterise. Per the pasqal-cloud
        # README: when a batch has no batch-level sequence, all jobs must
        # carry their own ``serialized_sequence``.
        jobs: list[Any] = [
            {"runs": shots, "serialized_sequence": _serialize_run_input(item)} for item in inputs
        ]

        device_type = self._resolve_device_type(DeviceTypeName)
        serialized_config = _serialize_backend_configuration(backend_configuration)

        try:
            batch = self._client.create_batch(
                serialized_sequence=None,
                jobs=jobs,
                device_type=device_type,
                wait=wait,
                tags=tags,
                backend_configuration=serialized_config,
            )
        except _pasqal_cloud_errors() as exc:
            raise PasqalDeviceError(
                f"Failed to submit batch to Pasqal device '{self.id}': {exc}"
            ) from exc

        return PasqalJob(job_id=batch.id, client=self._client, device=self)

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
