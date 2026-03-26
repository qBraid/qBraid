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
Module defining OriginQ provider class.

"""
import logging
import os
from threading import Lock
from typing import Any, Optional

from qbraid._caching import cached_method
from qbraid.runtime.provider import QuantumProvider

from .device import SIMULATOR_BACKENDS, OriginDevice

logger = logging.getLogger(__name__)

_SERVICE_CACHE: dict[str, Any] = {}
_SERVICE_LOCK = Lock()


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
    """Return a cached QCloudService instance for the given API key."""
    # pylint: disable-next=import-outside-toplevel
    from pyqpanda3 import qcloud as qcloud_module

    with _SERVICE_LOCK:
        service = _SERVICE_CACHE.get(api_key)
        if service is None:
            service = qcloud_module.QCloudService(api_key=api_key)
            _SERVICE_CACHE[api_key] = service
    return service


def _get_qcloud_job(job_id: str, api_key: Optional[str] = None):
    """Instantiate a QCloudJob after ensuring the service is configured."""
    # pylint: disable-next=import-outside-toplevel
    from pyqpanda3 import qcloud as qcloud_module

    api_key = api_key or _resolve_api_key()
    _get_service(api_key)
    return qcloud_module.QCloudJob(job_id)


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

    @cached_method
    def get_device(self, device_id: str) -> OriginDevice:
        """Get a specific OriginQ device."""
        device_id = device_id.strip()
        backend = self.service.backend(device_id)
        return OriginDevice(
            profile=OriginDevice.build_profile(backend, device_id, device_id),
            backend=backend,
            backend_name=device_id,
            api_key=self._api_key,
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
