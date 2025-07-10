# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""Local device class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.result import Result
from qbraid.runtime.result_data import GateModelResultData

if TYPE_CHECKING:
    import qiskit.result


class LocalDevice(QuantumDevice):
    """Local device class."""

    def __init__(self, profile: TargetProfile, **kwargs):
        super().__init__(profile=profile, **kwargs)
        self.aer_simulator = AerSimulator()

    def status(self) -> DeviceStatus:
        return DeviceStatus.ONLINE

    def transform(self, circuit: QuantumCircuit) -> QuantumCircuit:
        """Transform a circuit for the local device."""
        return transpile(circuit, self.aer_simulator)

    def submit(self, program: QuantumCircuit | list[QuantumCircuit], **kwargs) -> Result:
        """Run a program on the local device."""
        job = self.aer_simulator.run(program, **kwargs)
        result: qiskit.result.Result = job.result()
        counts = result.get_counts(program)
        return Result(
            device_id=self.id,
            job_id=job.job_id(),
            success=True,
            data=GateModelResultData(
                measurement_counts=counts,
            ),
            **kwargs,
        )
