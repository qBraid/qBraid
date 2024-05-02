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
import shutil
import subprocess
import time
import warnings
from typing import Dict, List, Optional

# from qbraid_core import QbraidClient
from qbraid_core.system import is_valid_semantic_version

from .exceptions import QirRunnerError
from .result import Result


class Simulator:
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

    def __init__(self, seed: Optional[int] = None, qir_runner_path: Optional[str] = None):
        self.seed = seed
        self._version = None
        self._qir_runner = None
        self.qir_runner = qir_runner_path
        if not is_valid_semantic_version(self.version):
            warnings.warn(
                f"Invalid qir-runner version '{self.version}' detected. Executable may be corrupt."
            )

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
                error_message = "No value was provided for the qir_runner_path, \
                                and the qir-runner executable was not found in the system PATH."
            else:
                error_message = f"The provided qir-runner executable path '{value}' does not exist."
            raise FileNotFoundError(error_message)

        self._qir_runner = resolved_path
        self._version = None  # Reset version cache since qir_runner changed

    @property
    def version(self) -> str:
        """Get the version of the qir-runner executable, caching the result."""
        if self._version is None:
            if self._qir_runner is None:
                raise ValueError("qir-runner path is not set.")
            output = self._execute_subprocess(
                [self.qir_runner, "--version"], stderr=subprocess.STDOUT
            )
            self._version = output.strip().split()[-1]
        return self._version

    @staticmethod
    def _execute_subprocess(command: List[str], text: bool = True, **kwargs) -> str:
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

    def run(
        self, file_name: str, entrypoint: Optional[str] = None, shots: Optional[int] = None
    ) -> Dict[str, List[int]]:
        """Runs the qir-runner executable with the given QIR file and shots.

        Args:
            file_name (str): Path to the QIR file to run ('.ll' or '.bc' file extension)
            entrypoint (optional, str): Name of the entrypoint function to execute in the QIR file.
            shots (optional, int): The number of times to repeat the execution of the chosen entry
                                   point in the program. Defaults to 1.

        Returns:
            A dictionary mapping 'qubit_i' to a list of measurement results.
        """
        # Build the command with required and optional arguments
        command = [self.qir_runner, "--shots", str(shots), "-f", file_name]
        if entrypoint:
            command.extend(["-e", entrypoint])
        if self.seed is not None:
            command.extend(["-r", str(self.seed)])

        # Execute the qir-runner with the built command
        start = time.time()
        raw_out = self._execute_subprocess(command)
        stop = time.time()
        miliseconds = int((stop - start) * 1000)
        return Result(raw_out, execution_duration=miliseconds)

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
