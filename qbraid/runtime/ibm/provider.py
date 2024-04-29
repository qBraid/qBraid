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
import re
from abc import abstractmethod
from typing import TYPE_CHECKING, Union

from qbraid.runtime.provider import QuantumProvider

from .device import QiskitBackend

if TYPE_CHECKING:
    import qiskit_ibm_provider
    import qiskit_ibm_runtime

    import qbraid.runtime.ibm


class QiskitRemoteService(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the IBM Quantum services.

    Attributes:
        qiskit_ibm_token (str): IBM Quantum token for authenticating with IBM Quantum services.
    """

    def __init__(self, qiskit_ibm_token=None, **kwargs):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            qiskit_ibm_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self.qiskit_ibm_token = qiskit_ibm_token or os.getenv("QISKIT_IBM_TOKEN")
        self._provider = self._get_ibm_provider(**kwargs)

    @abstractmethod
    def _get_ibm_provider(self, **kwargs):
        """Returns the IBM Quantum provider."""

    def get_devices(self, operational=True, **kwargs) -> list["qbraid.runtime.ibm.QiskitBackend"]:
        """Returns the IBM Quantum provider backends."""
        backends = self._provider.backends(operational=operational, **kwargs)
        return [QiskitBackend(backend) for backend in backends]

    def get_device(self, device_id: str) -> "qbraid.runtime.ibm.QiskitBackend":
        """Returns the IBM Quantum provider backends."""
        provider = self._get_ibm_provider()
        backend = provider.get_backend(device_id)
        return QiskitBackend(backend)

    @staticmethod
    def ibm_to_qbraid_id(name: str) -> str:
        """Converts IBM device name to qBraid device ID"""
        if name.startswith("ibm") or name.startswith("ibmq_"):
            return re.sub(r"^(ibm)(q)?_(.*)", r"\1_q_\3", name)
        return "ibm_q_" + name

    @abstractmethod
    def native_least_busy(
        self,
    ) -> Union["qiskit_ibm_provider.IBMBackend", "qiskit_ibm_runtime.IBMBackend"]:
        """Return the Backend object of the least busy qpu."""

    def ibm_least_busy_qpu(self) -> "qbraid.runtime.ibm.QiskitBackend":
        """Return the qBraid ID of the least busy IBMQ QPU."""
        backend = self.native_least_busy()
        return QiskitBackend(backend)


class QiskitProvider(QiskitRemoteService):
    """Wrapper for qiskit_ibm_provider.IBMProvider class"""

    def save_config(self):
        """Save the current configuration."""
        provider = self._get_ibm_provider()
        provider.save_account(token=self.qiskit_ibm_token, overwrite=True)

    def _get_ibm_provider(self, **kwargs) -> "qiskit_ibm_provider.IBMProvider":
        """Returns the IBM Quantum provider."""
        from qiskit_ibm_provider import IBMProvider  # pylint: disable=import-outside-toplevel

        return IBMProvider(token=self.qiskit_ibm_token, **kwargs)

    def native_least_busy(self) -> "qiskit_ibm_provider.IBMBackend":
        """Return the qBraid ID of the least busy IBMQ QPU."""
        from qiskit_ibm_provider import least_busy  # pylint: disable=import-outside-toplevel

        backends = self.get_devices(simulator=False, operational=True)
        return least_busy(backends)


class QiskitRuntime(QiskitRemoteService):
    """Wrapper for qiskit_ibm_runtime.QiskitRuntimeService class."""

    def _get_ibm_provider(
        self, channel: str = "ibm_quantum", **kwargs
    ) -> "qiskit_ibm_runtime.QiskitRuntimeService":
        """Returns the IBM Qiskt Runtime service."""
        # pylint: disable-next=import-outside-toplevel
        from qiskit_ibm_runtime import QiskitRuntimeService

        return QiskitRuntimeService(token=self.qiskit_ibm_token, channel=channel, **kwargs)

    def native_least_busy(self) -> "qiskit_ibm_runtime.IBMBackend":
        """Return the qBraid ID of the least busy IBMQ QPU."""
        return self._provider.least_busy(simulator=False, operational=True)
