# Copyright 2025 qBraid
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
Module containing top-level qbraid program loader functionality
utilizing entrypoints via ``importlib``.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Union

import openqasm3

from qbraid._entrypoints import load_entrypoint
from qbraid.exceptions import QbraidError

from .alias_manager import get_program_type_alias
from .exceptions import ProgramLoaderError
from .registry import QPROGRAM

if TYPE_CHECKING:
    from qbraid.programs.ahs import AnalogHamiltonianProgram
    from qbraid.programs.annealing import AnnealingProgram
    from qbraid.programs.gate_model import GateModelProgram


def load_program(
    program: QPROGRAM,
) -> Union[GateModelProgram, AnalogHamiltonianProgram, AnnealingProgram]:
    """Apply qbraid quantum program wrapper to a supported quantum program.

    This function is used to create a qBraid :class:`~qbraid.programs.QuantumProgram`
    object, which can then be transpiled to any supported quantum circuit-building package.
    The input quantum circuit object must be an instance of a circuit object derived from a
    supported package.

    Args:
        program: A supported quantum circuit/program object.

    Returns:
        QuantumProgram: A wrapped quantum program object of the inferred subclass.

    Raises:
        :class:`~qbraid.ProgramLoaderError`: If the input circuit is not a supported quantum program

    """
    if isinstance(program, openqasm3.ast.Program):
        program = openqasm3.dumps(program)

    try:
        package = get_program_type_alias(program)
    except QbraidError as err:
        raise ProgramLoaderError(f"Error loading quantum program of type {type(program)}") from err

    try:
        load_program_class = load_entrypoint("programs", package)
    except Exception as err:
        raise ProgramLoaderError(f"Error loading quantum program of type {type(program)}") from err

    program_instance = load_program_class(program)

    return program_instance
