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

"""Shared validation for Cirq conversion functions."""

import cirq

from qbraid.transpiler.exceptions import ProgramConversionError


def _validate_resolved_parameters(circuit: cirq.Circuit, target: str) -> None:
    """Reject unresolved parameters before entering a concrete conversion.

    Args:
        circuit: Cirq circuit to validate.
        target: Name of the concrete target format.

    Raises:
        ProgramConversionError: If the circuit contains unresolved parameters.
    """
    parameters = sorted(cirq.parameter_names(circuit))
    if parameters:
        names = ", ".join(parameters)
        raise ProgramConversionError(
            f"Cannot convert a Cirq circuit to {target} with unresolved parameters: {names}. "
            "Resolve the parameters before conversion."
        )
