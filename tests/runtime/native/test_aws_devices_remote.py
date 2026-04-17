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
Remote tests for running jobs on AWS devices through
the native QbraidProvider.
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

import numpy as np
import pytest

# from qbraid.runtime import QbraidProvider, DeviceStatus, Result, JobStatus, AnalogResultData

if TYPE_CHECKING:
    import braket.ahs.analog_hamiltonian_simulation as braket_ahs

braket_found = importlib.util.find_spec("braket") is not None


@pytest.fixture
def ahs_program() -> braket_ahs.AnalogHamiltonianSimulation:
    """Analogue Hamiltonian Simulation program."""
    # pylint: disable=import-outside-toplevel
    from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
    from braket.ahs.atom_arrangement import AtomArrangement
    from braket.ahs.driving_field import DrivingField
    from braket.timings.time_series import TimeSeries

    # pylint: enable=import-outside-toplevel

    separation = 5e-6
    block_separation = 15e-6
    k_max = 5
    m_max = 5

    register = AtomArrangement()
    for k in range(k_max):
        for m in range(m_max):
            register.add((block_separation * m, block_separation * k + separation / np.sqrt(3)))
            register.add(
                (
                    block_separation * m - separation / 2,
                    block_separation * k - separation / (2 * np.sqrt(3)),
                )
            )
            register.add(
                (
                    block_separation * m + separation / 2,
                    block_separation * k - separation / (2 * np.sqrt(3)),
                )
            )

    omega_const = 1.5e7  # rad/s
    rabi_pulse_area = np.pi / np.sqrt(3)  # rad
    omega_slew_rate_max = 400000000000000.0  # rad/s^2
    time_separation_min = 5e-08  # s

    amplitude = TimeSeries.trapezoidal_signal(
        rabi_pulse_area,
        omega_const,
        0.99 * omega_slew_rate_max,
        time_separation_min=time_separation_min,
    )

    detuning = TimeSeries.constant_like(amplitude, 0.0)
    phase = TimeSeries.constant_like(amplitude, 0.0)

    drive = DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)
    ahs_program = AnalogHamiltonianSimulation(register=register, hamiltonian=drive)

    return ahs_program


# @pytest.mark.remote
# @pytest.mark.skipif(not braket_found, reason="braket not installed")
# def test_submit_ahs_program_to_aquila(ahs_program: braket_ahs.AnalogHamiltonianSimulation):
#     """Test submitting an AHS program to the Aquila device."""
#     provider = QbraidProvider()
#     device = provider.get_device("aws:quera:qpu:aquila")
#     status = device.status()
#     if status != DeviceStatus.ONLINE:
#         pytest.skip(f"{device.id} is {status.value}")

#     job = device.run(ahs_program, shots=100)
#     assert job.status() == JobStatus.COMPLETED
#     result = job.result()
#     assert isinstance(result, Result)
#     assert isinstance(result.data, AnalogResultData)
#     assert result.data.get_counts() == {"00": 60, "11": 40}
