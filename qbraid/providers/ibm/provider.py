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
from typing import TYPE_CHECKING, List

from qiskit_ibm_provider import IBMProvider, least_busy

if TYPE_CHECKING:
    import qiskit_ibm_provider


class QiskitProvider:
    """
    This class is responsible for managing the interactions and
    authentications with the IBM Quantum services.

    Attributes:
        qiskit_ibm_token (str): IBM Quantum token for authenticating with IBM Quantum services.
    """

    def __init__(self, qiskit_ibm_token=None):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            qiskit_ibm_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self.qiskit_ibm_token = qiskit_ibm_token or os.getenv("QISKIT_IBM_TOKEN")
        self._provider = self._get_ibm_provider()

    def save_config(self):
        """Save the current configuration."""
        raise NotImplementedError

    def _get_ibm_provider(self) -> "qiskit_ibm_provider.IBMProvider":
        """Returns the IBM Quantum provider."""
        return IBMProvider(token=self.qiskit_ibm_token)

    def get_devices(self, operational=True, **kwargs) -> List["qiskit_ibm_provider.IBMBackend"]:
        """Returns the IBM Quantum provider backends."""
        return self._provider.backends(operational=operational, **kwargs)

    def get_device(self, device_id: str) -> "qiskit_ibm_provider.IBMBackend":
        """Returns the IBM Quantum provider backends."""
        provider = self._get_ibm_provider()
        return provider.get_backend(device_id)

    @staticmethod
    def ibm_to_qbraid_id(name: str) -> str:
        """Converts IBM device name to qBraid device ID"""
        if name.startswith("ibm") or name.startswith("ibmq_"):
            return re.sub(r"^(ibm)(q)?_(.*)", r"\1_q_\3", name)
        return "ibm_q_" + name

    def ibm_least_busy_qpu(self) -> str:
        """Return the qBraid ID of the least busy IBMQ QPU."""
        backends = self.get_devices(simulator=False, operational=True)
        backend = least_busy(backends)
        ibm_id = backend.name  # QPU name of form `ibm_*` or `ibmq_*`
        _, name = ibm_id.split("_")
        return f"ibm_q_{name}"
