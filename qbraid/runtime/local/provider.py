# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""Local provider class."""

from __future__ import annotations

from qiskit import QuantumCircuit

from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import LocalDevice

LOCAL_DEVICE_PROFILES = {
    "aer_simulator": TargetProfile(
        device_id="aer_simulator",
        simulator=True,
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=None,
        program_spec=ProgramSpec(
            QuantumCircuit, alias="qiskit", experiment_type=ExperimentType.GATE_MODEL
        ),
        provider_name="Qiskit",
        noise_models=None,
    )
}


class LocalProvider(QuantumProvider):
    """Local provider class."""

    def get_device(self, device_id: str) -> LocalDevice:
        """Get a specific local device."""
        if device_id not in LOCAL_DEVICE_PROFILES:
            raise ValueError(f"Device {device_id} not found.")
        profile = LOCAL_DEVICE_PROFILES[device_id]
        return LocalDevice(profile)

    def get_devices(self) -> list[LocalDevice]:
        """Get a list of local devices."""
        return [LocalDevice(profile) for profile in LOCAL_DEVICE_PROFILES.values()]
