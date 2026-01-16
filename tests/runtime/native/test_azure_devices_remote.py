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
Remote tests for running jobs on Azure Quantum devices through
the native QbraidProvider.
"""

from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

import numpy as np
import pytest

from qbraid.runtime import DeviceStatus, JobStatus, QbraidProvider, Result
from qbraid.runtime.result_data import AnalogResultData, GateModelResultData

pyquil_found = importlib.util.find_spec("pyquil") is not None
pulser_found = importlib.util.find_spec("pulser") is not None

if TYPE_CHECKING:
    import pulser as pulser_
    import pyquil as pyquil_


@pytest.fixture
def pulser_sequence() -> pulser_.Sequence:
    """Fixture for a Pulser sequence."""
    # pylint: disable=import-outside-toplevel
    import pulser
    from pulser.waveforms import BlackmanWaveform, RampWaveform

    # pylint: enable=import-outside-toplevel

    qubits = {
        "q0": (0, 0),
        "q1": (0, 10),
        "q2": (8, 2),
        "q3": (1, 15),
        "q4": (-10, -3),
        "q5": (-8, 5),
    }
    reg = pulser.Register(qubits)

    seq = pulser.Sequence(reg, pulser.devices.DigitalAnalogDevice)
    seq.declare_channel("ch0", "rydberg_global")
    amp_wf = BlackmanWaveform(1000, np.pi)
    det_wf = RampWaveform(1000, -5, 5)
    pulse = pulser.Pulse(amp_wf, det_wf, 0)
    seq.add(pulse, "ch0")

    return seq


@pytest.mark.remote
@pytest.mark.skipif(not pulser_found, reason="pulser not installed")
def test_submit_pulser_sequence_to_pasqal(pulser_sequence: pulser_.Sequence):
    """Test running a Pulser sequence on the Pasqal emulator."""
    provider = QbraidProvider()

    device = provider.get_device("azure:pasqal:sim:emu-tn")

    status = device.status()
    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

    job = device.run(pulser_sequence, shots=100)

    result = job.result()

    assert isinstance(result.data, AnalogResultData)

    counts: dict[str, int] = result.data.get_counts()

    assert all(len(k) == 6 for k in counts)
    assert sum(counts.values()) == 100


@pytest.fixture
@pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")
def pyquil_program() -> pyquil_.Program:
    """Fixture for a PyQuil program."""
    # pylint: disable=import-outside-toplevel
    import pyquil
    import pyquil.gates

    # pylint: enable=import-outside-toplevel

    p = pyquil.Program()
    ro = p.declare("ro", "BIT", 2)
    p += pyquil.gates.H(0)
    p += pyquil.gates.CNOT(0, 1)
    p += pyquil.gates.MEASURE(0, ro[0])
    p += pyquil.gates.MEASURE(1, ro[1])

    return p


@pytest.mark.remote
@pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")
def test_submit_quil_to_rigetti(pyquil_program: pyquil_.Program):
    """Test submitting a pyQuil program to run on the Rigetti simulator."""
    provider = QbraidProvider()

    device = provider.get_device("azure:rigetti:sim:qvm")
    status = device.status()

    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

    job = device.run(pyquil_program, shots=100)

    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    counts = result.data.get_counts()
    assert len(counts) == 2
    assert all(len(k) == 2 for k in counts)
    assert sum(counts.values()) == 100
