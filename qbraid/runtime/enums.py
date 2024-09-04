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
Module defining all :mod:`~qbraid.runtime` enumerated types.

"""
from enum import Enum


class DeviceActionType(Enum):
    """
    Enumeration for the quantum device action types
    supported natively by qBraid.

    Attributes:
        OPENQASM (str): Actions compatible with OpenQASM (gate-model).
        AHS (str): Actions using analog Hamiltonian simulation.
        ANNEALING (str): Actions using quantum annealing.
    """

    OPENQASM = "qbraid.programs.circuits"
    AHS = "qbraid.programs.ahs"


class DeviceStatus(Enum):
    """Enumeration for representing various operational statuses of devices.

    Attributes:
        ONLINE (str): Device is online and accepting jobs.
        UNAVAILABLE (str): Device is online but not accepting jobs.
        OFFLINE (str): Device is offline.
        RETIRED (str): Device has been retired and is no longer operational.
    """

    ONLINE = "online"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"
    RETIRED = "retired"


class NoiseModel(Enum):
    """Enumeration representing various noise models for quantum simulators.

    Attributes:
        NoNoise (str): The simulation is performed without any noise, representing an
            ideal quantum computer.
        Depolarizing (str): Applies random errors to qubits, effectively turning a pure
            quantum state into a mixed state.
        AmplitudeDamping (str): Simulates energy loss in a quantum system, causing qubits
            to decay from the excited state to the ground state.
        PhaseDamping (str): Represents dephasing, where the relative phase between quantum
            states is randomized without energy loss.
        BitFlip (str): Randomly flips the state of qubits (i.e., from 0 to 1 or from 1 to 0)
            with a certain probability.
        PhaseFlip (str): Randomly flips the phase of a qubit state (i.e., it applies a Z gate)
            with a certain probability.

    """

    NoNoise = "no_noise"
    Depolarizing = "depolarizing"
    AmplitudeDamping = "amplitude_damping"
    PhaseDamping = "phase_damping"
    BitFlip = "bit_flip"
    PhaseFlip = "phase_flip"


class JobStatus(Enum):
    """Enum for the status of processes (i.e. quantum jobs / tasks) resulting
    from any :meth:`~qbraid.runtime.QuantumDevice.run` method.

    Displayed status text values may differ from those listed below to provide
    additional visibility into tracebacks, particularly for failed jobs.

    Attributes:
        INITIALIZING (str): job is being initialized
        QUEUED (str): job is queued
        VALIDATING (str): job is being validated
        RUNNING (str): job is actively running
        CANCELLING (str): job is being cancelled
        CANCELLED (str): job has been cancelled
        COMPLETED (str): job has successfully run
        FAILED (str): job failed / incurred error
        UNKNOWN (str): job status is unknown/undetermined
        HOLD (str): job terminal but results witheld due to account status

    """

    def __new__(cls, value: str, default_message: str):
        """Customize Enum to accept two values: `value` and `default_message`."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.default_message = default_message
        obj.status_message = None
        return obj

    def set_status_message(self, message: str):
        """Set a custom message for the enum instance."""
        self.status_message = message

    def __repr__(self):
        """Custom repr to show custom message or default."""
        message = self.status_message if self.status_message else self.default_message
        return f"<{self.name}: '{message}'>"

    INITIALIZING = ("INITIALIZING", "job is being initialized")
    QUEUED = ("QUEUED", "job is queued")
    VALIDATING = ("VALIDATING", "job is being validated")
    RUNNING = ("RUNNING", "job is actively running")
    CANCELLING = ("CANCELLING", "job is being cancelled")
    CANCELLED = ("CANCELLED", "job has been cancelled")
    COMPLETED = ("COMPLETED", "job has successfully run")
    FAILED = ("FAILED", "job failed / incurred error")
    UNKNOWN = ("UNKNOWN", "job status is unknown/undetermined")
    HOLD = ("HOLD", "job terminal but results witheld due to account status")


JOB_STATUS_FINAL = (JobStatus.COMPLETED, JobStatus.CANCELLED, JobStatus.FAILED)
