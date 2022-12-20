# Copyright 2023 qBraid
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
Module for drawing quantum circuit diagrams

"""
from typing import TYPE_CHECKING

from qbraid.exceptions import ProgramTypeError

if TYPE_CHECKING:
    import qbraid


def draw(program: "qbraid.QPROGRAM") -> None:
    """Draws circuit diagram.

    Args:
        :data:`~.qbraid.QPROGRAM`: Supported quantum program

    Raises:
        ProgramTypeError: If quantum program is not of a supported type
    """

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    if "qiskit" in package:
        print(program.draw())

    elif "braket" in package or "cirq" in package or "pyquil" in package:
        print(program)

    else:
        raise ProgramTypeError(program)
