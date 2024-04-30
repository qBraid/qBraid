# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for configuring provider credentials and authentication.

"""

import os
from typing import TYPE_CHECKING, Optional

from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.accounts import ChannelType

from qbraid.runtime.provider import QuantumProvider

from .device import QiskitBackend

if TYPE_CHECKING:
    import qiskit_ibm_runtime

    import qbraid.runtime.ibm


class QiskitRuntimeProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the IBM Quantum services.

    Attributes:
        token (str): IBM Cloud API key or IBM Quantum API token.
        runtime_service (qiskit_ibm_runtime.QiskitRuntimeService): IBM Quantum runtime service.
    """

    def __init__(self, token: Optional[str] = None, channel: ChannelType = "ibm_quantum", **kwargs):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            token (str, optional): IBM Quantum token. Defaults to None.
        """
        self.token = token or os.getenv("QISKIT_IBM_TOKEN")
        self._runtime_service = QiskitRuntimeService(token=self.token, channel=channel, **kwargs)

    @property
    def runtime_service(self) -> "qiskit_ibm_runtime.QiskitRuntimeService":
        """Returns the IBM Quantum runtime service."""
        return self._runtime_service

    @staticmethod
    def save_config(
        token: Optional[str] = None, channel: Optional[str] = None, overwrite: bool = True, **kwargs
    ) -> None:
        """Saves IBM runtime service account to disk for future use."""
        token = token or os.getenv("QISKIT_IBM_TOKEN")
        channel = channel or os.getenv("QISKIT_IBM_CHANNEL", "ibm_quantum")
        QiskitRuntimeService.save_account(
            token=token, channel=channel, overwrite=overwrite, **kwargs
        )

    def get_devices(self, operational=True, **kwargs) -> list["qbraid.runtime.ibm.QiskitBackend"]:
        """Returns the IBM Quantum provider backends."""
        backends = self.runtime_service.backends(operational=operational, **kwargs)
        return [QiskitBackend(backend) for backend in backends]

    def get_device(
        self, device_id: str, instance: Optional[str] = None
    ) -> "qbraid.runtime.ibm.QiskitBackend":
        """Returns the IBM Quantum provider backends."""
        backend = self.runtime_service.backend(device_id, instance=instance)
        return QiskitBackend(backend)

    def least_busy(
        self, simulator=False, operational=True, **kwargs
    ) -> "qbraid.runtime.ibm.QiskitBackend":
        """Return the least busy IBMQ QPU."""
        backend = self.runtime_service.least_busy(
            simulator=simulator, operational=operational, **kwargs
        )
        return QiskitBackend(backend)
