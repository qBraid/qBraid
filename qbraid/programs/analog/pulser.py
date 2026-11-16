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
Module defining the PulserSequence program wrapper.

"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pulser import Sequence
from qbraid_core.services.runtime.schemas import Program

from qbraid.programs.exceptions import ProgramTypeError, TransformError

from ._model import AnalogHamiltonianProgram

if TYPE_CHECKING:
    import pulser

    import qbraid.runtime


class PulserSequence(AnalogHamiltonianProgram):
    """Wrapper class for ``pulser.Sequence`` objects."""

    def __init__(self, program: pulser.Sequence):
        super().__init__(program)
        if not isinstance(program, Sequence):
            raise ProgramTypeError(
                message=f"Expected 'pulser.Sequence' object, got '{type(program)}'."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the sequence's Pulser abstract representation."""
        return json.loads(self.program.to_abstract_repr())

    @property
    def num_atoms(self) -> int:
        """Return the number of atoms in the register, mappable or not."""
        return len(self.program.get_register(include_mappable=True).qubit_ids)

    def serialize(self) -> Program:
        """Return the program in a format suitable for submission to the qBraid API."""
        return Program(format="pulser.sequence", data={"sequence_builder": self.to_dict()})

    def transform(self, device: qbraid.runtime.QuantumDevice) -> None:
        """Move the sequence onto the Pulser device of the Pasqal QPU ``device`` runs on.

        Pasqal moves every QPU sequence onto the QPU's own device and validates it there, so a
        sequence built on another device, such as ``AnalogDevice``, is rejected after it has
        been queued. Moving it here reports the reason before submitting. Emulators, and QPUs
        whose specs cannot be read, are left to Pasqal.

        Raises:
            TransformError: If the QPU would reject the sequence.
        """
        # pylint: disable-next=import-outside-toplevel
        from qbraid.runtime.pasqal.specs import (
            PASQAL_PUBLIC_SPECS_URL,
            get_pasqal_qpu_device,
            pasqal_device_type,
            quiet_pulser_warnings,
        )

        if device.simulator:
            return
        device_type = pasqal_device_type(device.id)
        target = get_pasqal_qpu_device(device_type)
        if target is None:
            return

        sequence: Sequence = self.program
        guidance = (
            f"Build the sequence on Pasqal's {device_type} Pulser device (its specs are public "
            f"at {PASQAL_PUBLIC_SPECS_URL}; load them with pulser's deserialize_device) and "
            "define the register from one of its calibrated layouts "
            "(device.calibrated_register_layouts)."
        )

        if not sequence.is_register_mappable():
            register = sequence.register
            if target.requires_layout and register.layout is None:
                raise TransformError(
                    f"{device_type} requires the sequence's register to be defined from a "
                    f"RegisterLayout. {guidance}"
                )
            try:
                with quiet_pulser_warnings():
                    Sequence(register, target)
            except Exception as err:  # pylint: disable=broad-exception-caught
                raise TransformError(
                    f"The sequence's register is not valid on {device_type}: {_reason(err)} "
                    f"{guidance}"
                ) from err

        if sequence.device.name == target.name:
            return
        # Non-strict, as Pasqal moves sequences: a strict switch also rejects sequences that
        # differ only in device properties Pasqal does not require to match, e.g. Rydberg level.
        move = getattr(sequence, "with_new_device", None) or sequence.switch_device
        try:
            with quiet_pulser_warnings():
                self._program = move(target, strict=False)
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise TransformError(
                f"The sequence is not valid on {device_type}: {_reason(err)} {guidance}"
            ) from err


def _reason(err: Exception) -> str:
    """The error's message, or its type when Pulser raised it without one."""
    return str(err).strip() or type(err).__name__
