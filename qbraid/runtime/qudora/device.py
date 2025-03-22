# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining QUDORA device class

"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Optional

from qbraid.programs.typer import QasmStringType, get_qasm_type_alias
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.qudora


class QUDORABackend(QuantumDevice):
    """QUDORA backend class."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.qudora.QUDORASession,
        **kwargs,
    ):
        super().__init__(profile=profile, **kwargs)
        self._session = session
        if "shots" not in self._options:
            self._options.update_options(shots=100)
            self._options.set_validator("shots", lambda x: 0 < x <= self.profile.max_shots)

    @property
    def session(self) -> qbraid.runtime.qudora.QUDORASession:
        """Returns the session for the device."""
        return self._session

    def status(self):
        """Returns the status of the device."""
        data = self._session.get_device(self.id)
        is_online: bool = data.get("is_online", False)

        if is_online:
            return DeviceStatus.ONLINE

        return DeviceStatus.OFFLINE

    def show_available_settings(self) -> None:
        """Shows available settings for this backend."""
        available_settings = self.profile.get("available_settings", {})

        if not available_settings:
            print("There are no available options for this backend")
        else:
            example_settings = {}

            for key in available_settings:
                example_settings[key] = available_settings[key]["default"]

            print(
                f"\n Available Options for backend {self.id}:\n\n"
                f"{json.dumps(available_settings, indent=2)}\n\n"
                f"You can set these parameters by passing a dictionary to the "
                f"QUDORABackend.run() method.\n"
                f"Below is an example settings dictionary:\n"
                f"{json.dumps(example_settings, indent=1)}"
            )

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: QasmStringType | list[QasmStringType],
        job_name: Optional[str] = None,
        backend_settings: Optional[dict] = None,
        **kwargs,
    ):
        """Submits a given circuit to the QUDORA Cloud.

        Args:
            run_input (QasmStringType | list[QasmStringType]): Circuit(s) to run.
            job_name (str, optional): Name of the job.
                Defaults to "Job from qBraid Runtime".
            backend_settings (dict, optional): Additional settings for the Backend.
                Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            QUDORAJob: Object referencing the job in the QUDORA Cloud.
        """
        if not isinstance(run_input, list):
            run_input = [run_input]

        max_circuits = self.profile["max_programs_per_job"]
        if len(run_input) > max_circuits:
            raise RuntimeError(
                f"Provided {len(run_input)} circuits to QUDORABackend.run(). "
                f"Backend only supports {max_circuits} circuits per job."
            )

        shots = kwargs.get("shots", self._options.get("shots", 100))
        if isinstance(shots, int):
            shots = [shots] * len(run_input)

        program_types = {get_qasm_type_alias(program) for program in run_input}
        if len(program_types) > 1:
            raise ValueError("All programs must be of the same type, either 'qasm2' or 'qasm3'.")

        program_type = program_types.pop()
        language_map = {"qasm2": "OpenQASM2", "qasm3": "OpenQASM3"}
        language = language_map.get(program_type)
        if language is None:
            raise ValueError("Program type not recognized. Must be 'qasm2' or 'qasm3'.")

        json_data = {
            "name": job_name or "Job from qBraid Runtime",
            "language": language,
            "shots": shots,
            "target": self.profile["username"],
            "input_data": run_input,
            "backend_settings": backend_settings,
        }

        job_id = self.session.create_job(json_data)

        return job_id

    def __str__(self):
        """String representation of the QUDORADevice object."""
        return f"{self.__class__.__name__}('{self.id}')"
