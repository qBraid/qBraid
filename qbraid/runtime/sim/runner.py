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
Module containing Python wrapper for the qir-runner sparse quantum state simulator.

"""
import logging
import pathlib
import shutil
import subprocess
import time
import warnings
from collections import defaultdict
from typing import TYPE_CHECKING, Optional

import numpy as np
from qbraid_core.system import is_valid_semantic_version

from qbraid.programs import QPROGRAM_REGISTRY, ProgramSpec
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus, DeviceType
from qbraid.runtime.profile import RuntimeProfile

from .exceptions import QirRunnerError
from .result import Result

if TYPE_CHECKING:
    import pyqir

    import qbraid.runtime

logger = logging.getLogger(__name__)

SPEC = None if "pyqir" not in QPROGRAM_REGISTRY else ProgramSpec(QPROGRAM_REGISTRY["pyqir"])
PROFILE = RuntimeProfile(
    device_type=DeviceType.SIMULATOR,
    device_id="qbraid_qir_simulator",
    num_qubits=64,
    program_spec=SPEC,
)


class Simulator(QuantumDevice):
    """A sparse simulator that extends the functionality of the qir-runner.

    This simulator is a Python wrapper for the qir-runner, a command-line tool
    for executing compiled QIR files. It uses sparse matrices to represent quantum
    states and can be used to simulate quantum circuits that have been compiled to QIR.
    The simulator allows for setting a seed for random number generation and specifying
    an entry point for the execution.

    The qir-runner can be found at: https://github.com/qir-alliance/qir-runner

    Attributes:
        seed (optional, int): The value to use when seeding the random number generator used
                              for quantum simulation.
        qir_runner (str): Path to the qir-runner executable.
        version (str): The version of the qir-runner executable.
    """

    def __init__(
        self,
        profile: "qbraid.runtime.RuntimeProfile" = PROFILE,
        seed: Optional[int] = None,
        qir_runner_path: Optional[str] = None,
    ):
        """Create a QIR runner simulator."""
        super().__init__(profile=profile)
        self.seed = seed
        self._version = None
        self._qir_runner = None
        self.qir_runner = qir_runner_path

    @property
    def qir_runner(self) -> str:
        """Path to the qir-runner executable."""
        return self._qir_runner

    @qir_runner.setter
    def qir_runner(self, value: Optional[str]) -> None:
        """Set the qir-runner path with additional validation."""
        resolved_path = shutil.which(value or "qir-runner")
        if resolved_path is None:
            if value is None:
                logger.info(
                    "No value was provided for the qir_runner_path, and the qir-runner executable was not found in the system PATH."
                )
            else:
                logger.info("The provided qir-runner executable path '%s' does not exist.", value)

        self._qir_runner = resolved_path
        self._version = None  # Reset version cache since qir_runner changed

    @property
    def version(self) -> str:
        """Get the version of the qir-runner executable, caching the result."""
        if self._version is None and self._qir_runner is not None:
            output = self._execute_subprocess(
                [self.qir_runner, "--version"], stderr=subprocess.STDOUT
            )
            runner_version = output.strip().split()[-1]
            if not is_valid_semantic_version(runner_version):
                warnings.warn(
                    f"Invalid qir-runner version '{runner_version}' detected. Executable may be corrupt."
                )
                runner_version = None
            self._version = runner_version
        return self._version

    def status(self):
        """Check the status of the qir-runner executable."""
        if self.qir_runner is None or self.version is None:
            return DeviceStatus.UNAVAILABLE

        return DeviceStatus.ONLINE

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the backend"""
        return 0

    @staticmethod
    def _execute_subprocess(command: list[str], text: bool = True, **kwargs) -> str:
        """Execute a subprocess command and return its output.

        Args:
            command (list): The command to execute as a list of arguments.

        Returns:
            str: The output from the command execution.

        Raises:
            QirRunnerError: If there's an error executing the command.
        """
        try:
            return subprocess.check_output(command, text=text, **kwargs)
        except (subprocess.CalledProcessError, OSError) as err:
            raise QirRunnerError(f"Error executing qir-runner command: {command}") from err

    @staticmethod
    def _parse_results(stdout: str) -> dict[str, list[int]]:
        """Parse the raw output from the execution to extract measurement results."""
        results = defaultdict(list)
        current_shot_results = []

        for line in stdout.splitlines():
            elements = line.split()
            if len(elements) == 3 and elements[:2] == ["OUTPUT", "RESULT"]:
                _, _, bit = elements
                current_shot_results.append(int(bit))
            elif line.startswith("END"):
                for idx, result in enumerate(current_shot_results):
                    results[f"q{idx}"].append(result)
                current_shot_results = []

        return dict(results)

    @staticmethod
    def _data_to_measurements(parsed_data: dict) -> np.ndarray:
        """Convert parsed data to a 2D array of measurement results."""
        return np.array([parsed_data[key] for key in sorted(parsed_data.keys())], dtype=np.int8).T

    def submit(
        self, module: "pyqir.Module", entrypoint: Optional[str] = None, shots: Optional[int] = None
    ) -> Result:
        """Runs the qir-runner executable with the given QIR file and shots.

        Args:
            module (pyqir.Module): QIR module to run in the simulator.
            entrypoint (optional, str): Name of the entrypoint function to execute in the QIR file.
            shots (optional, int): The number of times to repeat the execution of the chosen entry
                                   point in the program. Defaults to 1.

        Returns:
            Result: The results of the simulation execution.
        """
        filename_prefix = pathlib.Path(module.source_filename).stem
        file_dir = pathlib.Path.cwd()

        # Create the directory if it doesn't exist
        file_dir.mkdir(exist_ok=True)

        # Construct file paths using pathlib
        bc_file = file_dir / f"{filename_prefix}.bc"

        try:
            # Save bitcode file (does not require an encoding)
            with open(bc_file, "wb") as file:
                file.write(module.bitcode)

            command = [self.qir_runner, "--shots", str(shots or 1), "-f", str(bc_file)]
            if entrypoint:
                command.extend(["-e", entrypoint])
            if self.seed is not None:
                command.extend(["-r", str(self.seed)])

            # Execute the qir-runner with the built command
            start = time.time()
            raw_out = self._execute_subprocess(command)
            stop = time.time()
            milliseconds = int((stop - start) * 1000)
            parsed_data = self._parse_results(raw_out)
            measurements = self._data_to_measurements(parsed_data)
            return Result(measurements, execution_duration=milliseconds)
        finally:
            # Ensure the bitcode file is deleted even if an error occurs
            bc_file.unlink(missing_ok=True)

    def __eq__(self, other):
        """Check if two Simulator instances are equal based on their attributes."""
        if not isinstance(other, Simulator):
            return NotImplemented
        return (
            (self.seed == other.seed)
            and (self.qir_runner == other.qir_runner)
            and (self.version == other.version)
        )

    def __repr__(self):
        return f"Simulator(seed={self.seed}, qir_runner={self.qir_runner}, version={self.version})"
