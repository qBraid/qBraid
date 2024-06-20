# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=import-outside-toplevel,redefined-outer-name

"""
Unit tests for the serialization and deserialization of the AHS program IR.

"""

from decimal import Decimal
from typing import Union

import numpy as np
import pytest


@pytest.fixture
def ahs_program():
    """Return an example AHS program."""
    from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
    from braket.ahs.atom_arrangement import AtomArrangement
    from braket.ahs.driving_field import DrivingField
    from braket.timings.time_series import TimeSeries

    a = 5.7e-6  # nearest-neighbor separation (in meters)

    register = AtomArrangement()
    register.add(np.array([0.5, 0.5 + 1 / np.sqrt(2)]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([-0.5, 0.5 + 1 / np.sqrt(2)]) * a)

    # smooth transition from "down" to "up" state
    time_max = 4e-6  # seconds
    time_ramp = 1e-7  # seconds
    omega_max = 6300000.0  # rad / sec
    delta_start = -5 * omega_max
    delta_end = 5 * omega_max

    omega = TimeSeries()
    omega.put(0.0, 0.0)
    omega.put(time_ramp, omega_max)
    omega.put(time_max - time_ramp, omega_max)
    omega.put(time_max, 0.0)

    delta = TimeSeries()
    delta.put(0.0, delta_start)
    delta.put(time_ramp, delta_start)
    delta.put(time_max - time_ramp, delta_end)
    delta.put(time_max, delta_end)

    phi = TimeSeries().put(0.0, 0.0).put(time_max, 0.0)

    drive = DrivingField(amplitude=omega, phase=phi, detuning=delta)

    return AnalogHamiltonianSimulation(register=register, hamiltonian=drive)


def serialize_register(register):
    """Serialize an AtomArrangement object to a dictionary."""
    return {
        "sites": [[str(value) for value in sublist] for sublist in register.sites],
        "filling": register.filling,
    }


def deserialize_register(register):
    """Deserialize a dictionary to an AtomArrangement object."""
    from braket.ir.ahs import AtomArrangement

    return AtomArrangement(
        sites=[[Decimal(value) for value in sublist] for sublist in register["sites"]],
        filling=register["filling"],
    )


def serialize_hamiltonian(hamiltonian) -> dict:
    """Serialize a Hamiltonian object to a dictionary."""
    return {
        "drivingFields": [
            {
                "amplitude": serialize_physical_field(field.amplitude),
                "phase": serialize_physical_field(field.phase),
                "detuning": serialize_physical_field(field.detuning),
            }
            for field in hamiltonian.drivingFields
        ],
        "localDetuning": hamiltonian.localDetuning,
    }


def serialize_physical_field(field) -> dict:
    """Serialize a PhysicalField object to a dictionary."""
    return {
        "time_series": {
            "values": [str(v) for v in field.time_series.values],
            "times": [str(t) for t in field.time_series.times],
        },
        "pattern": field.pattern,
    }


def create_time_series(values: list[str], times: list[str]):
    """Create a TimeSeries object from lists of values and times."""
    from braket.ir.ahs import TimeSeries

    if len(values) != len(times):
        raise ValueError("The values and times lists must have the same length.")
    return TimeSeries(values=[Decimal(v) for v in values], times=[Decimal(t) for t in times])


def create_physical_field(values: list[str], times: list[str], pattern: Union[str, list[float]]):
    """Create a PhysicalField object from lists of values and times."""
    from braket.ir.ahs import PhysicalField

    time_series = create_time_series(values, times)
    return PhysicalField(time_series=time_series, pattern=pattern)


def create_driving_field(amplitude_info, phase_info, detuning_info):
    """
    Create a DrivingField object from lists of values and times for
    the amplitude, phase, and detuning.

    """
    from braket.ir.ahs import DrivingField

    amplitude = create_physical_field(*amplitude_info)
    phase = create_physical_field(*phase_info)
    detuning = create_physical_field(*detuning_info)
    return DrivingField(amplitude=amplitude, phase=phase, detuning=detuning)


def deserialize_hamiltonian(data: dict):
    """Deserialize a dictionary to a Hamiltonian object."""
    from braket.ir.ahs import Hamiltonian

    fields = [
        create_driving_field(
            (
                field["amplitude"]["time_series"]["values"],
                field["amplitude"]["time_series"]["times"],
                field["amplitude"]["pattern"],
            ),
            (
                field["phase"]["time_series"]["values"],
                field["phase"]["time_series"]["times"],
                field["phase"]["pattern"],
            ),
            (
                field["detuning"]["time_series"]["values"],
                field["detuning"]["time_series"]["times"],
                field["detuning"]["pattern"],
            ),
        )
        for field in data["drivingFields"]
    ]
    return Hamiltonian(drivingFields=fields, localDetuning=data["localDetuning"])


def test_serialize_register(ahs_program):
    """Test the serialization and deserialization of an AtomArrangement object."""
    register_ir = ahs_program._register_to_ir()
    register_data = serialize_register(register_ir)
    register_reconstructed = deserialize_register(register_data)
    assert register_ir == register_reconstructed


def test_serialize_hamiltonian(ahs_program):
    """Test the serialization and deserialization of an AnalogHamiltonianSimulation object."""
    hamiltonian_ir = ahs_program._hamiltonian_to_ir()
    hamiltonian_data = serialize_hamiltonian(hamiltonian_ir)
    ham_reconstructed = deserialize_hamiltonian(hamiltonian_data)
    assert hamiltonian_ir == ham_reconstructed
