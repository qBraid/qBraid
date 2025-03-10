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
Unit tests for converting Bloqade programs to Amazon Braket AHS

"""
from __future__ import annotations

import importlib.util
from typing import TYPE_CHECKING

import numpy as np
import pytest

# Skip all tests if bloqade not installed
bloqade_found = importlib.util.find_spec("bloqade") is not None
if bloqade_found:
    from bloqade.analog import var  # type: ignore
    from bloqade.analog.atom_arrangement import Square  # type: ignore

if TYPE_CHECKING:
    from bloqade.analog.builder.assign import BatchAssign  # type: ignore

pytestmark = pytest.mark.skipif(not bloqade_found, reason="bloqade not installed")

from qbraid.programs.ahs.braket_ahs import BraketAHS  # noqa: F821
from qbraid.transpiler.conversions.braket_ahs import bloqade_to_braket_ahs  # noqa: F821


@pytest.fixture
def bloqade_program() -> BatchAssign:
    """Create a Bloqade program batch."""

    adiabatic_durations = [0.4, 3.2, 0.4]

    max_detuning = var("max_detuning")
    adiabatic_program = (
        Square(3, lattice_spacing="lattice_spacing")
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            durations=adiabatic_durations, values=[0.0, "max_rabi", "max_rabi", 0.0]
        )
        .detuning.uniform.piecewise_linear(
            durations=adiabatic_durations,
            values=[
                -max_detuning,  # scalar variables support direct arithmetic operations
                -max_detuning,
                max_detuning,
                max_detuning,
            ],
        )
        .assign(max_rabi=15.8, max_detuning=16.33)
        .batch_assign(lattice_spacing=np.arange(4.0, 7.0, 0.5))
    )

    return adiabatic_program


@pytest.fixture
def ahs_program_batch0() -> dict:
    return {
        "register": {
            "sites": [
                ["0.000000", "0.000000"],
                ["0.000000", "0.0000040"],
                ["0.000000", "0.0000080"],
                ["0.0000040", "0.000000"],
                ["0.0000040", "0.0000040"],
                ["0.0000040", "0.0000080"],
                ["0.0000080", "0.000000"],
                ["0.0000080", "0.0000040"],
                ["0.0000080", "0.0000080"],
            ],
            "filling": [1, 1, 1, 1, 1, 1, 1, 1, 1],
        },
        "hamiltonian": {
            "drivingFields": [
                {
                    "amplitude": {
                        "time_series": {
                            "values": ["0E+5", "1.58E+7", "1.58E+7", "0E+5"],
                            "times": ["0.000000", "4E-7", "0.0000036", "0.0000040"],
                        },
                        "pattern": "uniform",
                    },
                    "phase": {
                        "time_series": {"values": ["0", "0"], "times": ["0.000000", "0.0000040"]},
                        "pattern": "uniform",
                    },
                    "detuning": {
                        "time_series": {
                            "values": ["-1.633E+7", "-1.633E+7", "1.633E+7", "1.633E+7"],
                            "times": ["0.000000", "4E-7", "0.0000036", "0.0000040"],
                        },
                        "pattern": "uniform",
                    },
                }
            ],
            "localDetuning": [],
        },
    }


def test_convert_bloqade_to_braket_ahs(bloqade_program, ahs_program_batch0):
    """Test converting Bloqade program to Amazon Braket AHS."""
    braket_ahs_program_batch = bloqade_to_braket_ahs(bloqade_program)
    braket_ahs_program = braket_ahs_program_batch[0]
    wrapped_ahs_program = BraketAHS(braket_ahs_program)
    assert wrapped_ahs_program.to_dict() == ahs_program_batch0
