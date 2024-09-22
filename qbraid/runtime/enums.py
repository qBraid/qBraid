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
from __future__ import annotations

from enum import Enum


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


class ExperimentType(Enum):
    """
    Enumeration for quantum experiment types.

    Attributes:
        GATE_MODEL (str): Gate-based quantum computing (e.g., OpenQASM).
        AHS (str): Analog Hamiltonian simulation.
        ANNEALING (str): Quantum annealing for optimization problems.
        PHOTONIC_MODEL (str): Photonic quantum computing using photons as qubits.
        OTHER (str): Placeholder for other or unspecified quantum computing models.
    """

    GATE_MODEL = "gate_model"
    AHS = "analog_hamiltonian_simulation"
    ANNEALING = "quantum_annealing"
    PHOTONIC_MODEL = "photonic_quantum_computing"
    OTHER = "other"


class NoiseModel(Enum):
    """Enumeration representing various noise models for quantum simulators.

    Attributes:
        Ideal (str): The simulation is performed without any noise, representing an
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

    Ideal = "no_noise"
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

    """

    def __new__(cls, value: str):
        """Enumeration representing the status of a :py:class:`QuantumJob`."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.default_message = cls._get_default_message(value)
        obj.status_message = None
        return obj

    @classmethod
    def _get_default_message(cls, status: str) -> str:
        """Get the default message for a given status value."""
        default_messages = {
            "INITIALIZING": "job is being initialized",
            "QUEUED": "job is queued",
            "VALIDATING": "job is being validated",
            "RUNNING": "job is actively running",
            "CANCELLING": "job is being cancelled",
            "CANCELLED": "job has been cancelled",
            "COMPLETED": "job has successfully run",
            "FAILED": "job failed / incurred error",
            "UNKNOWN": "job status is unknown/undetermined",
            "HOLD": "job terminal but results withheld due to account status",
        }
        message = default_messages.get(status)

        if message is None:
            raise ValueError(f"Invalid status value: {status}")

        return message

    def set_status_message(self, message: str) -> None:
        """Set a custom message for the enum instance."""
        self.status_message = message

    def __repr__(self):
        """Custom repr to show custom message or default."""
        message = self.status_message if self.status_message else self.default_message
        return f"<{self.name}: '{message}'>"

    def __call__(self) -> JobStatus:
        """Create a new instance of the enum member, allowing unique attributes."""
        obj = self.__class__(self._value_)
        obj.default_message = self.default_message
        return obj

    @classmethod
    def terminal_states(cls) -> set[JobStatus]:
        """Returns the final job statuses."""
        return {cls.COMPLETED, cls.CANCELLED, cls.FAILED}

    INITIALIZING = "INITIALIZING"
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    HOLD = "HOLD"
