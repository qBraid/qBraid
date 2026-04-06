# Copyright (C) 2026 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining OriginQ provider class.

"""
import logging
import os
from typing import TYPE_CHECKING, Any, Optional

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider
from qbraid.transpiler.conversions.qasm2.qasm2_extras import qasm2_to_pyqpanda3

from .device import SIMULATOR_BACKENDS, OriginDevice

if TYPE_CHECKING:
    from pyqpanda3.qcloud import QCloudBackend

logger = logging.getLogger(__name__)


def _resolve_api_key(explicit_key: Optional[str] = None) -> str:
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


def _get_service(api_key: str):
    """Return a QCloudService instance for the given API key."""
    # pylint: disable-next=import-outside-toplevel
    from pyqpanda3 import qcloud as qcloud_module

    return qcloud_module.QCloudService(api_key=api_key)


def _get_qcloud_job(job_id: str, service: Optional[Any] = None):
    """Instantiate a QCloudJob after ensuring the service is configured."""
    # pylint: disable-next=import-outside-toplevel
    from pyqpanda3 import qcloud as qcloud_module

    if service is None:
        api_key = _resolve_api_key()
        service = _get_service(api_key)
    return qcloud_module.QCloudJob(job_id)


def _infer_num_qubits(backend: QCloudBackend, backend_name: str, *, simulator: bool) -> int | None:
    """Infer qubit count from chip info or simulator mapping."""
    if simulator:
        return SIMULATOR_BACKENDS.get(backend_name)
    try:
        chip_info = backend.chip_info()
        return chip_info.qubits_num()
    except Exception:
        logger.debug("Unable to determine qubit count from chip info", exc_info=True)
        return None


def _infer_basis_gates(backend: QCloudBackend, *, simulator: bool) -> list[str] | None:
    """Infer basis gates from chip info for hardware devices."""
    if simulator:
        return None
    try:
        chip_info = backend.chip_info()
        return chip_info.get_basic_gates()
    except Exception:
        logger.debug("Unable to determine basis gates from chip info", exc_info=True)
        return None


class OriginProvider(QuantumProvider):
    """OriginQ QCloud provider class."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = _resolve_api_key(api_key)
        self._service = None

    @property
    def service(self):
        """Return the QCloudService instance, creating it on first access."""
        if self._service is None:
            self._service = _get_service(self._api_key)
        return self._service

    def _build_profile(
        self,
        backend: QCloudBackend,
        device_id: str,
        backend_name: str,
    ) -> TargetProfile:
        """Build a TargetProfile from an OriginQ backend."""
        # pylint: disable-next=import-outside-toplevel
        from pyqpanda3.core import QProg

        simulator = backend_name in SIMULATOR_BACKENDS
        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=_infer_num_qubits(backend, backend_name, simulator=simulator),
            program_spec=ProgramSpec(QProg, alias="pyqpanda3", serialize=qasm2_to_pyqpanda3),
            basis_gates=_infer_basis_gates(backend, simulator=simulator),
            provider_name="origin",
        )

    @cached_method
    def get_device(self, device_id: str) -> OriginDevice:
        """Get a specific OriginQ device."""
        device_id = device_id.strip()
        backend = self.service.backend(device_id)
        return OriginDevice(
            profile=self._build_profile(backend, device_id, device_id),
            backend=backend,
            backend_name=device_id,
            service=self.service,
        )

    @cached_method
    def get_devices(self, *, hardware_only: Optional[bool] = None, **kwargs) -> list[OriginDevice]:
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
