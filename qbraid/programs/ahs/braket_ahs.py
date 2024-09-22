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
Module defining AnalogHamiltonianProgram Class

"""
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Union

import braket.ir.ahs as ir
from braket.ahs import AnalogHamiltonianSimulation, Field

from qbraid.programs.exceptions import ProgramTypeError

from ._model import AnalogHamiltonianProgram

if TYPE_CHECKING:
    import braket.ahs

    import qbraid.runtime.aws


class BraketAHS(AnalogHamiltonianProgram):
    """Wrapper class for ``braket.ahs.AnalogHamiltonianSimulation`` objects."""

    def __init__(self, program: braket.ahs.AnalogHamiltonianSimulation):
        super().__init__(program)
        if not isinstance(program, AnalogHamiltonianSimulation):
            raise ProgramTypeError(
                message=f"Expected 'ahs.AnalogHamiltonianSimulation' object, got '{type(program)}'."
            )

    def to_dict(self) -> dict:
        return BraketAHSEncoder().encode_ahs(self.program)

    def transform(self, device: "qbraid.runtime.aws.BraketDevice") -> None:
        """Transform program to according to device target profile."""
        if not device.simulator:
            program: AnalogHamiltonianSimulation = self.program
            self._program = program.discretize(device._device)


class BraketAHSEncoder:
    """Class for encoding AnalogHamiltonianSimulation objects to dictionaries."""

    def encode_register(self, register: ir.AtomArrangement) -> dict:
        """Convert an AtomArrangement object to a dictionary."""
        return {
            "sites": [[str(value) for value in sublist] for sublist in register.sites],
            "filling": register.filling,
        }

    def encode_field(self, field: Union[ir.PhysicalField, Field]) -> dict:
        """Convert a PhysicalField object to a dictionary."""
        return {
            "time_series": {
                "values": [str(v) for v in field.time_series.values],
                "times": [str(t) for t in field.time_series.times],
            },
            "pattern": field.pattern,
        }

    def encode_hamiltonian(self, hamiltonian: ir.Hamiltonian) -> dict:
        """Convert a Hamiltonian object to a dictionary."""
        return {
            "drivingFields": [
                {
                    "amplitude": self.encode_field(field.amplitude),
                    "phase": self.encode_field(field.phase),
                    "detuning": self.encode_field(field.detuning),
                }
                for field in hamiltonian.drivingFields
            ],
            "localDetuning": [
                {
                    "magnitude": self.encode_field(term.magnitude),
                }
                for term in hamiltonian.localDetuning
            ],
        }

    def encode_ahs(self, program: AnalogHamiltonianSimulation) -> dict:
        """Convert an AnalogHamiltonianSimulation object to a dictionary."""
        program_ir = program.to_ir()

        return {
            "register": self.encode_register(program_ir.setup.ahs_register),
            "hamiltonian": self.encode_hamiltonian(program_ir.hamiltonian),
        }


class BraketAHSDecoder:
    """Class for decoding AnalogHamiltonianSimulation objects from dictionaries."""

    def decode_time_series(self, values: list[str], times: list[str]) -> ir.TimeSeries:
        """Create a TimeSeries object from lists of values and times."""
        if len(values) != len(times):
            raise ValueError("The values and times lists must have the same length.")
        return ir.TimeSeries(values=[Decimal(v) for v in values], times=[Decimal(t) for t in times])

    def decode_physical_field(
        self, values: list[str], times: list[str], pattern: Union[str, list[float]]
    ) -> ir.PhysicalField:
        """Create a PhysicalField object from lists of values and times."""
        time_series = self.decode_time_series(values, times)
        return ir.PhysicalField(time_series=time_series, pattern=pattern)

    def decode_driving_field(self, amplitude_info, phase_info, detuning_info) -> ir.DrivingField:
        """
        Create a DrivingField object from lists of values and times for
        the amplitude, phase, and detuning.

        """
        amplitude = self.decode_physical_field(*amplitude_info)
        phase = self.decode_physical_field(*phase_info)
        detuning = self.decode_physical_field(*detuning_info)
        return ir.DrivingField(amplitude=amplitude, phase=phase, detuning=detuning)

    def decode_local_detuning(self, magnitude_info) -> ir.LocalDetuning:
        """
        Create a LocalDetuning object from lists of values and times for
        the magnitude.

        """
        magnitude = self.decode_physical_field(*magnitude_info)
        return ir.LocalDetuning(magnitude=magnitude)

    def decode_register(self, register: dict) -> ir.AtomArrangement:
        """Convert a dictionary to an AtomArrangement object."""
        return ir.AtomArrangement(
            sites=[[Decimal(value) for value in sublist] for sublist in register["sites"]],
            filling=register["filling"],
        )

    def decode_hamiltonian(self, data: dict) -> ir.Hamiltonian:
        """Convert a dictionary to a Hamiltonian object."""
        driving_fields = [
            self.decode_driving_field(
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

        local_detunings = [
            self.decode_local_detuning(
                (
                    term["magnitude"]["time_series"]["values"],
                    term["magnitude"]["time_series"]["times"],
                    term["magnitude"]["pattern"],
                )
            )
            for term in data["localDetuning"]
        ]

        return ir.Hamiltonian(drivingFields=driving_fields, localDetuning=local_detunings)

    def decode_ahs(self, data: dict) -> AnalogHamiltonianSimulation:
        """Convert a dictionary to an AnalogHamiltonianSimulation object."""
        register = self.decode_register(data["register"])
        hamiltonian = self.decode_hamiltonian(data["hamiltonian"])
        program_ir = ir.Program(setup=ir.Setup(ahs_register=register), hamiltonian=hamiltonian)
        return AnalogHamiltonianSimulation.from_ir(program_ir)
