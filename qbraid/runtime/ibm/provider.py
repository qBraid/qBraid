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
Module for configuring IBM provider credentials and authentication.

"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

import qiskit
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.accounts import ChannelType

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.profile import TargetProfile
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
        runtime_service (qiskit_ibm_runtime.QiskitRuntimeService): IBM Quantum runtime service.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        instance: Optional[str] = None,
        channel: Optional[ChannelType] = None,
        **kwargs,
    ):
        """
        Initializes the QiskitRuntimeProvider object with IBM Quantum credentials.

        Args:
            token (str, optional): IBM Cloud API key.
            instance (str, optional): The service instance to use.
                This is the Cloud Resource Name (CRN) or the service name. If set, it will define
                a default instance for service instantiation. If not set, the service will fetch
                all instances accessible within the account.
            channel (ChannelType, optional): ``ibm_cloud``, ``ibm_quantum_platform`` or ``local``.
                If ``local``, uses testing mode and primitive queries will run on local simulator.
        """
        self.token = token or os.getenv("QISKIT_IBM_TOKEN")
        self.instance = instance or os.getenv("QISKIT_IBM_INSTANCE")
        self.channel = channel or os.getenv("QISKIT_IBM_CHANNEL", "ibm_quantum_platform")
        self._runtime_service = QiskitRuntimeService(
            channel=self.channel, token=self.token, instance=self.instance, **kwargs
        )

    @property
    def runtime_service(self) -> qiskit_ibm_runtime.QiskitRuntimeService:
        """Returns the IBM Quantum runtime service."""
        return self._runtime_service

    def save_config(
        self,
        token: Optional[str] = None,
        instance: Optional[str] = None,
        channel: Optional[ChannelType] = None,
        overwrite: bool = True,
        **kwargs,
    ) -> None:
        """Saves IBM runtime service account to disk for future use."""
        token = token or self.token
        instance = instance or self.instance
        channel = channel or self.channel
        QiskitRuntimeService.save_account(
            token=token, instance=instance, channel=channel, overwrite=overwrite, **kwargs
        )

    def _build_runtime_profile(
        self, backend: qiskit_ibm_runtime.IBMBackend, program_spec: Optional[ProgramSpec] = None
    ) -> TargetProfile:
        """Builds a runtime profile from a backend."""
        program_spec = program_spec or ProgramSpec(qiskit.QuantumCircuit)
        config = backend.configuration()

        local = config.local
        simulator = config.local or config.simulator

        return TargetProfile(
            device_id=backend.name,
            simulator=simulator,
            local=local,
            num_qubits=config.n_qubits,
            program_spec=program_spec,
            instance=backend._instance,
            max_shots=config.max_shots,
            provider_name="IBM",
            experiment_type=ExperimentType.GATE_MODEL,
            basis_gates=config.basis_gates,
        )

    @cached_method
    def get_devices(self, operational=True, **kwargs) -> list[qbraid.runtime.ibm.QiskitBackend]:
        """Returns the IBM Quantum provider backends."""

        backends = self.runtime_service.backends(operational=operational, **kwargs)
        program_spec = ProgramSpec(qiskit.QuantumCircuit)
        return [
            QiskitBackend(
                profile=self._build_runtime_profile(backend, program_spec=program_spec),
                service=self.runtime_service,
            )
            for backend in backends
        ]

    @cached_method
    def get_device(
        self, device_id: str, instance: Optional[str] = None
    ) -> qbraid.runtime.ibm.QiskitBackend:
        """Returns the IBM Quantum provider backends."""
        backend = self.runtime_service.backend(device_id, instance=instance)
        return QiskitBackend(
            profile=self._build_runtime_profile(backend), service=self.runtime_service
        )

    def least_busy(
        self, simulator=False, operational=True, **kwargs
    ) -> qbraid.runtime.ibm.QiskitBackend:
        """Return the least busy IBMQ QPU."""
        backend = self.runtime_service.least_busy(
            simulator=simulator, operational=operational, **kwargs
        )
        return QiskitBackend(
            profile=self._build_runtime_profile(backend), service=self.runtime_service
        )

    def __hash__(self):
        if not hasattr(self, "_hash"):
            object.__setattr__(self, "_hash", hash((self.token, self.channel)))
        return self._hash  # pylint: disable=no-member
