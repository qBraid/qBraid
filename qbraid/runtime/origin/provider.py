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
Module defining OriginQ provider class.

"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import OriginDevice

if TYPE_CHECKING:
    from pyqpanda3.qcloud import QCloudBackend, QCloudService

logger = logging.getLogger(__name__)

SIMULATOR_BACKENDS: dict[str, int] = {
    "full_amplitude": 35,
    "partial_amplitude": 68,
    "single_amplitude": 200,
}


def _resolve_api_key(explicit_key: str | None = None) -> str:
    """Resolve the OriginQ API key from explicit input or environment variable."""
    if explicit_key:
        return explicit_key
    value = os.getenv("ORIGIN_API_KEY")
    if value:
        return value
    raise ValueError(
        "An OriginQ API key is required. "
        "Please provide it directly as an argument or set it via "
        "the ORIGIN_API_KEY environment variable."
    )


def _get_service(api_key: str) -> QCloudService:
    """Return a QCloudService instance for the given API key."""
    # pylint: disable-next=import-outside-toplevel
    from pyqpanda3 import qcloud as qcloud_module

    return qcloud_module.QCloudService(api_key=api_key)


def _infer_num_qubits(backend: QCloudBackend) -> int | None:
    """Infer qubit count from chip info or simulator mapping."""
    backend_name = backend.name()
    if backend_name.endswith("amplitude"):
        return SIMULATOR_BACKENDS.get(backend_name)
    chip_info = backend.chip_info()
    return chip_info.qubits_num()


def _infer_basis_gates(backend: QCloudBackend) -> list[str] | None:
    """Infer basis gates from chip info for hardware devices."""
    backend_name = backend.name()
    if backend_name.endswith("amplitude"):
        return None

    try:
        chip_info = backend.chip_info()
        return chip_info.get_basic_gates()
    except Exception:  # pylint: disable=broad-exception-caught
        logger.debug("Unable to determine basis gates from chip info", exc_info=True)
        return None


class OriginProvider(QuantumProvider):
    """OriginQ QCloud provider class."""

    def __init__(self, api_key: str | None = None):
        self._api_key = _resolve_api_key(api_key)
        self._service = None

    @property
    def service(self) -> QCloudService:
        """Return the QCloudService instance, creating it on first access."""
        if self._service is None:
            self._service = _get_service(self._api_key)
        return self._service

    def _build_profile(self, backend: QCloudBackend) -> TargetProfile:
        """Build a TargetProfile from an OriginQ backend."""
        # pylint: disable-next=import-outside-toplevel
        from pyqpanda3.core import QProg

        device_id = backend.name()
        simulator = device_id in SIMULATOR_BACKENDS
        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=_infer_num_qubits(backend),
            program_spec=ProgramSpec(QProg, alias="pyqpanda3"),
            basis_gates=_infer_basis_gates(backend),
            provider_name="origin",
        )

    @cached_method
    def get_device(self, device_id: str) -> OriginDevice:
        """Get a specific OriginQ device."""
        device_id = device_id.strip()
        backend = self.service.backend(device_id)
        return OriginDevice(
            profile=self._build_profile(backend),
            backend=backend,
            service=self.service,
        )

    @cached_method
    def get_devices(self, *, hardware_only: bool | None = None) -> list[OriginDevice]:
        """Get a list of available OriginQ devices."""
        catalog = self.service.backends()
        device_ids: set[str] = set()
        for backend_id, available in catalog.items():
            if available is False:
                continue
            if hardware_only and backend_id in SIMULATOR_BACKENDS:
                continue
            device_ids.add(backend_id)
        return [self.get_device(device_id) for device_id in sorted(device_ids)]

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash(self._api_key))
        return self._hash  # pylint: disable=no-member
