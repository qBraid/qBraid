# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for loading, encoding, and decoding AHS programs using Amazon Braket.

"""
import json

import numpy as np
import pytest
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.driving_field import DrivingField
from braket.ahs.field import Field
from braket.ahs.hamiltonian import Hamiltonian
from braket.ahs.local_detuning import LocalDetuning
from braket.ahs.pattern import Pattern
from braket.timings.time_series import TimeSeries

from qbraid.programs import ProgramTypeError, load_program
from qbraid.programs.ahs import AHSEncoder
from qbraid.programs.ahs.braket_ahs import BraketAHS, BraketAHSDecoder, BraketAHSEncoder


@pytest.fixture
def register_data() -> dict:
    """Return example register data."""
    return {
        "sites": [
            ["0.00000285", "0.00000688050865276332"],
            ["0.00000688050865276332", "0.00000285"],
            ["0.00000688050865276332", "-0.00000285"],
            ["0.00000285", "-0.00000688050865276332"],
            ["-0.00000285", "-0.00000688050865276332"],
            ["-0.00000688050865276332", "-0.00000285"],
            ["-0.00000688050865276332", "0.00000285"],
            ["-0.00000285", "0.00000688050865276332"],
        ],
        "filling": [1, 1, 1, 1, 1, 1, 1, 1],
    }


@pytest.fixture
def hamiltonian_data():
    """Return example Hamiltonian data."""
    return {
        "drivingFields": [
            {
                "amplitude": {
                    "time_series": {
                        "values": ["0.0", "6300000.0", "6300000.0", "0.0"],
                        "times": ["0.0", "1E-7", "0.0000039", "0.000004"],
                    },
                    "pattern": "uniform",
                },
                "phase": {
                    "time_series": {"values": ["0.0", "0.0"], "times": ["0.0", "0.000004"]},
                    "pattern": "uniform",
                },
                "detuning": {
                    "time_series": {
                        "values": ["-31500000.0", "-31500000.0", "31500000.0", "31500000.0"],
                        "times": ["0.0", "1E-7", "0.0000039", "0.000004"],
                    },
                    "pattern": "uniform",
                },
            }
        ],
        "localDetuning": [],
    }


@pytest.fixture
def ahs_data(register_data, hamiltonian_data):
    """Return example AHS data."""
    return {"register": register_data, "hamiltonian": hamiltonian_data}


@pytest.fixture
def ahs_program() -> AnalogHamiltonianSimulation:
    """Return an example AHS program."""
    a = 5.7e-6  # meters

    register = AtomArrangement()
    register.add(np.array([0.5, 0.5 + 1 / np.sqrt(2)]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([0.5 + 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5, -0.5 - 1 / np.sqrt(2)]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), -0.5]) * a)
    register.add(np.array([-0.5 - 1 / np.sqrt(2), 0.5]) * a)
    register.add(np.array([-0.5, 0.5 + 1 / np.sqrt(2)]) * a)

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


@pytest.fixture
def ahs_program_local_detuning() -> AnalogHamiltonianSimulation:
    """Return an example AHS program with local detuning."""
    a = 5.5e-6  # meters

    register = AtomArrangement()
    register.add([0, 0])
    register.add([a, 0.0])
    register.add([0.5 * a, np.sqrt(3) / 2 * a])

    omega_max = 2.5e6  # rad / seconds
    t_max = np.pi / (np.sqrt(2) * omega_max)  # seconds

    omega = TimeSeries()
    omega.put(0.0, omega_max)
    omega.put(t_max, omega_max)

    phi = TimeSeries().put(0.0, 0.0).put(t_max, 0.0)  # (time [s], value [rad])
    delta_global = TimeSeries().put(0.0, 0.0).put(t_max, 0.0)  # (time [s], value [rad/s])

    drive = DrivingField(amplitude=omega, phase=phi, detuning=delta_global)

    delta_local = TimeSeries()
    delta_local.put(0.0, -omega_max * 20)  # (time [s], value [rad/s])
    delta_local.put(t_max, -omega_max * 20)

    h = Pattern([0, 0, 0.5])

    local_detuning = LocalDetuning(magnitude=Field(time_series=delta_local, pattern=h))

    H = Hamiltonian()
    H += drive
    H += local_detuning

    return AnalogHamiltonianSimulation(hamiltonian=H, register=register)


@pytest.fixture
def ahs_fixture(request):
    """Return an AHS program fixture."""
    if request.param == "ahs_program":
        return request.getfixturevalue("ahs_program")
    if request.param == "ahs_program_local_detuning":
        return request.getfixturevalue("ahs_program_local_detuning")
    raise ValueError("Unsupported fixture")


@pytest.fixture
def encoder() -> BraketAHSEncoder:
    """Return a BraketAHSEncoder object."""
    return BraketAHSEncoder()


@pytest.fixture
def decoder() -> BraketAHSDecoder:
    """Return a BraketAHSDecoder object."""
    return BraketAHSDecoder()


@pytest.mark.parametrize(
    "ahs_fixture", ["ahs_program", "ahs_program_local_detuning"], indirect=True
)
def test_register_serialization(
    ahs_fixture: AnalogHamiltonianSimulation, encoder: BraketAHSEncoder, decoder: BraketAHSDecoder
):
    """Test the serialization and deserialization of an AtomArrangement object."""
    ahs_register_ir = ahs_fixture._register_to_ir()
    ahs_register_data = encoder.encode_register(ahs_register_ir)
    ahs_register_reconstructed = decoder.decode_register(ahs_register_data)
    assert ahs_register_ir == ahs_register_reconstructed


@pytest.mark.parametrize(
    "ahs_fixture", ["ahs_program", "ahs_program_local_detuning"], indirect=True
)
def test_hamiltonian_serialization(
    ahs_fixture: AnalogHamiltonianSimulation, encoder: BraketAHSEncoder, decoder: BraketAHSDecoder
):
    """Test the serialization and deserialization of an AnalogHamiltonianSimulation object."""
    ahs_hamiltonian_ir = ahs_fixture._hamiltonian_to_ir()
    ahs_hamiltonian_data = encoder.encode_hamiltonian(ahs_hamiltonian_ir)
    ahs_hamiltonian_reconstructed = decoder.decode_hamiltonian(ahs_hamiltonian_data)
    assert ahs_hamiltonian_ir == ahs_hamiltonian_reconstructed


@pytest.mark.parametrize(
    "ahs_fixture", ["ahs_program", "ahs_program_local_detuning"], indirect=True
)
def test_ahs_serialization(
    ahs_fixture: AnalogHamiltonianSimulation, encoder: BraketAHSEncoder, decoder: BraketAHSDecoder
):
    """Test the serialization and deserialization of an AnalogHamiltonianSimulation object."""
    ahs_data = encoder.encode_ahs(ahs_fixture)
    ahs_reconstructed = decoder.decode_ahs(ahs_data)
    assert ahs_fixture.to_ir() == ahs_reconstructed.to_ir()


def test_decode_time_series_raises_for_length_mismatch(decoder: BraketAHSDecoder):
    """Test that decoding a TimeSeries with mismatched lengths raises a ValueError."""
    with pytest.raises(ValueError):
        decoder.decode_time_series([0, 1], [0, 1, 2])


def test_braket_ahs_wrapper_attributes(ahs_program, register_data, hamiltonian_data, ahs_data):
    """Test the attributes of the BraketAHS wrapper."""
    program = BraketAHS(ahs_program)
    assert program.num_atoms == program.num_qubits == 8
    assert program.register == register_data
    assert program.hamiltonian == hamiltonian_data
    assert program.to_dict() == ahs_data


def test_ahs_program_encoding(ahs_program, ahs_data):
    """Test that AHSEncoder correctly encodes AnalogHamiltonianProgram."""
    program = BraketAHS(ahs_program)
    encoded_json = json.dumps(program, cls=AHSEncoder)
    assert json.loads(encoded_json) == ahs_data


def test_non_supported_type_encoding():
    """Test that encoding a non-supported type raises a TypeError."""
    with pytest.raises(TypeError):
        json.dumps({1, 2, 3}, cls=AHSEncoder)


def test_fallback_to_superclass():
    """Test that types not handled by AHSEncoder but supported by JSONEncoder are encoded."""
    data = {"key": [1, 2, 3]}
    encoded_json = json.dumps(data, cls=AHSEncoder)
    assert json.loads(encoded_json) == data


def test_load_braket_ahs_program(ahs_program):
    """Test loading a BraketAHS program."""
    program = load_program(ahs_program)
    assert isinstance(program, BraketAHS)


def test_braket_ahs_wrapper_equality(ahs_program, ahs_program_local_detuning, decoder):
    """Test equality comparison of the BraketAHS wrapper."""
    program_1 = BraketAHS(ahs_program)
    program_2 = BraketAHS(ahs_program_local_detuning)
    assert program_1 == BraketAHS(decoder.decode_ahs(program_1.to_dict()))
    assert program_1 != program_2
    assert program_1 != 42


def test_braket_ahs_wrapper_bad_type():
    """Test that creating a BraketAHS wrapper with a bad type raises a ProgramTypeError."""
    with pytest.raises(ProgramTypeError):
        BraketAHS(())
