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
Module defining IQM provider class

"""
import qiskit
from iqm.qiskit_iqm import IQMProvider as ClientProvider

from qbraid.programs.spec import ProgramSpec
from qbraid.runtime.enums import DeviceActionType, DeviceType
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import IQMDevice


class IQMProvider(QuantumProvider):
    """IQM provider class."""

    def __init__(self, token):
        super().__init__()
        self.token = token

    def _build_profile(self, data):
        """Build a profile for IQM device."""
        backend_num_qubits = {"deneb": 6, "garnet": 20}
        device_id = data
        return TargetProfile(
            device_id=device_id,
            device_type=DeviceType.QPU,
            action_type=DeviceActionType.OPENQASM,
            num_qubits=backend_num_qubits.get(device_id),
            program_spec=ProgramSpec(qiskit.QuantumCircuit, alias="qiskit"),
            device_name=device_id,
            endpoint_url="https://cocos.resonance.meetiqm.com/" + device_id,
            provider_name="IQM",
        )

    def get_devices(self, **kwargs):  # pylint: disable=unused-argument
        """Get all IQM devices."""
        devices = ["deneb", "garnet"]
        backends = [
            ClientProvider(
                url="https://cocos.resonance.meetiqm.com/" + device_name, token=self.token
            ).get_backend()
            for device_name in devices
        ]

        return [
            IQMDevice(profile=device, backend=backend)
            for (device, backend) in zip(devices, backends)
        ]

    def get_device(self, device_id: str):
        """Get an IQM device."""
        return ClientProvider(
            url="https://cocos.resonance.meetiqm.com/" + device_id, token=self.token
        ).get_backend()
