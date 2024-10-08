# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name,unused-argument

"""
Unit tests for submitting a Braket AHS job.

"""
import json
import uuid
from typing import Any, Optional, Union
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.driving_field import DrivingField
from braket.aws import AwsQuantumTask
from braket.aws.aws_quantum_task_batch import AwsQuantumTaskBatch
from braket.device_schema.quera.quera_device_capabilities_v1 import QueraDeviceCapabilities
from braket.devices import Devices
from braket.ir.ahs import Program
from braket.task_result import (
    AdditionalMetadata,
    AnalogHamiltonianSimulationShotMeasurement,
    AnalogHamiltonianSimulationShotMetadata,
    AnalogHamiltonianSimulationShotResult,
    AnalogHamiltonianSimulationTaskResult,
    TaskMetadata,
)
from braket.tasks import AnalogHamiltonianSimulationQuantumTaskResult
from braket.timings.time_series import TimeSeries

from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime import DeviceStatus, TargetProfile
from qbraid.runtime.aws.device import BraketDevice
from qbraid.runtime.aws.job import BraketQuantumTask
from qbraid.runtime.aws.provider import BraketProvider
from qbraid.runtime.aws.result_builder import BraketAhsResultBuilder, ResultDecodingError
from qbraid.runtime.exceptions import DeviceProgramTypeMismatchError

AQUILA_ARN = Devices.QuEra.Aquila
TASK_ARN = "arn:aws:braket:us-east-1:0123456789012:quantum-task/" + str(uuid.uuid4())

PARADIGM = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.quera.quera_ahs_paradigm_properties",
        "version": "1",
    },
    "qubitCount": 256,
    "lattice": {
        "area": {"width": 7.5e-05, "height": 7.6e-05},
        "geometry": {
            "spacingRadialMin": 4e-06,
            "spacingVerticalMin": 4e-06,
            "positionResolution": 1e-08,
            "numberSitesMax": 256,
        },
    },
    "rydberg": {
        "c6Coefficient": 5.42e-24,
        "rydbergGlobal": {
            "rabiFrequencyRange": [0.0, 15800000.0],
            "rabiFrequencyResolution": 400.0,
            "rabiFrequencySlewRateMax": 400000000000000.0,
            "detuningRange": [-125000000.0, 125000000.0],
            "detuningResolution": 0.2,
            "detuningSlewRateMax": 6000000000000000.0,
            "phaseRange": [-99.0, 99.0],
            "phaseResolution": 5e-07,
            "timeResolution": 1e-09,
            "timeDeltaMin": 5e-08,
            "timeMin": 0.0,
            "timeMax": 4e-06,
        },
    },
    "performance": {
        "lattice": {
            "positionErrorAbs": 2.25e-07,
            "sitePositionError": 1e-07,
            "atomPositionError": 2e-07,
            "fillingErrorTypical": 0.008,
            "fillingErrorWorst": 0.05,
            "vacancyErrorTypical": 0.001,
            "vacancyErrorWorst": 0.005,
            "atomLossProbabilityTypical": 0.005,
            "atomLossProbabilityWorst": 0.01,
            "atomCaptureProbabilityTypical": 0.001,
            "atomCaptureProbabilityWorst": 0.002,
            "atomDetectionErrorFalsePositiveTypical": 0.001,
            "atomDetectionErrorFalsePositiveWorst": 0.005,
            "atomDetectionErrorFalseNegativeTypical": 0.001,
            "atomDetectionErrorFalseNegativeWorst": 0.005,
        },
        "rydberg": {
            "rydbergGlobal": {
                "rabiFrequencyErrorRel": 0.03,
                "rabiFrequencyGlobalErrorRel": 0.02,
                "rabiFrequencyInhomogeneityRel": 0.02,
                "groundDetectionError": 0.05,
                "rydbergDetectionError": 0.1,
                "groundPrepError": 0.01,
                "rydbergPrepErrorBest": 0.05,
                "rydbergPrepErrorWorst": 0.07,
                "T1Single": 7.5e-05,
                "T1Ensemble": 7.5e-05,
                "T2StarSingle": 5e-06,
                "T2StarEnsemble": 4.75e-06,
                "T2EchoSingle": 8e-06,
                "T2EchoEnsemble": 7e-06,
                "T2RabiSingle": 8e-06,
                "T2RabiEnsemble": 7e-06,
                "T2BlockadedRabiSingle": 8e-06,
                "T2BlockadedRabiEnsemble": 7e-06,
                "detuningError": 1000000.0,
                "detuningInhomogeneity": 1000000.0,
                "rabiAmplitudeRampCorrection": [
                    {"rampTime": 5e-08, "rabiCorrection": 0.92},
                    {"rampTime": 7.5e-08, "rabiCorrection": 0.97},
                    {"rampTime": 1e-07, "rabiCorrection": 1.0},
                ],
            }
        },
    },
}

CAPABILITIES = {
    "service": {
        "braketSchemaHeader": {
            "name": "braket.device_schema.device_service_properties",
            "version": "1",
        },
        "executionWindows": [
            {"executionDay": "Monday", "windowStartHour": "01:00:00", "windowEndHour": "23:59:59"},
            {"executionDay": "Tuesday", "windowStartHour": "00:00:00", "windowEndHour": "12:00:00"},
            {
                "executionDay": "Wednesday",
                "windowStartHour": "00:00:00",
                "windowEndHour": "12:00:00",
            },
            {"executionDay": "Friday", "windowStartHour": "00:00:00", "windowEndHour": "23:59:59"},
            {
                "executionDay": "Saturday",
                "windowStartHour": "00:00:00",
                "windowEndHour": "23:59:59",
            },
            {"executionDay": "Sunday", "windowStartHour": "00:00:00", "windowEndHour": "12:00:00"},
        ],
        "shotsRange": [1, 1000],
        "deviceCost": {"price": 0.01, "unit": "shot"},
        "deviceLocation": "Boston, USA",
        "updatedAt": "2024-06-03T12:00:00+00:00",
    },
    "action": {"braket.ir.ahs.program": {"version": ["1"], "actionType": "braket.ir.ahs.program"}},
    "deviceParameters": {},
    "braketSchemaHeader": {
        "name": "braket.device_schema.quera.quera_device_capabilities",
        "version": "1",
    },
    "paradigm": PARADIGM,
}

METADATA = {
    "deviceArn": "arn:aws:braket:us-east-1::device/qpu/quera/Aquila",
    "deviceCapabilities": json.dumps(CAPABILITIES),
    "deviceName": "Aquila",
    "deviceQueueInfo": [
        {"queue": "QUANTUM_TASKS_QUEUE", "queuePriority": "Normal", "queueSize": "20"},
        {"queue": "QUANTUM_TASKS_QUEUE", "queuePriority": "Priority", "queueSize": "0"},
        {"queue": "JOBS_QUEUE", "queueSize": "0"},
    ],
    "deviceStatus": "ONLINE",
    "deviceType": "QPU",
    "providerName": "QuEra",
}


class MockBotoSession:
    """Mock Boto session class."""

    @property
    def region_name(self):
        """Return the region."""
        return "us-east-1"


class MockAwsSession:
    """Test class for AWS session."""

    @property
    def region(self):
        """Return the region."""
        return "us-east-1"

    @property
    def boto_session(self):
        """Return the boto session."""
        return MockBotoSession()

    def get_device(self, arn):  # pylint: disable=unused-argument
        """Returns metadata for a device."""
        return METADATA

    def create_quantum_task(self, **kwargs):
        """Creates a quantum task."""
        return TASK_ARN

    def get_quantum_task(self, *args, **kwargs):
        """Returns a quantum task."""
        return AwsQuantumTask(arn=TASK_ARN, aws_session=self)


class MockAquilaDevice:
    """Test class for braket device."""

    @property
    def arn(self):
        """Return the ARN of the device."""
        return METADATA["deviceArn"]

    @property
    def name(self):
        """Return the name of the device."""
        return METADATA["deviceName"]

    @property
    def aws_session(self):
        """Return the AWS session."""
        return MockAwsSession()

    @property
    def status(self):
        """Return the status of the device."""
        return METADATA["deviceStatus"]

    @property
    def is_available(self):
        """Return whether the device is available."""
        return True

    @property
    def properties(self):
        """Return the properties of the device."""
        return QueraDeviceCapabilities(**CAPABILITIES)

    @staticmethod
    def get_device_region(arn):
        """Returns the region of a device."""
        return "us-east-1"

    def run_batch(
        self, task_specifications: Union[Any, list[Any]], shots: Optional[int] = None, **kwargs
    ):
        """Executes a batch of quantum tasks in parallel."""
        return AwsQuantumTaskBatch(
            aws_session=self.aws_session,
            device_arn=AQUILA_ARN,
            task_specifications=task_specifications,
            s3_destination_folder=("amazon-braket-qbraid-jobs", "tasks"),
            shots=shots,
            max_parallel=10,
            poll_timeout_seconds=AwsQuantumTask.DEFAULT_RESULTS_POLL_TIMEOUT,
            poll_interval_seconds=AwsQuantumTask.DEFAULT_RESULTS_POLL_INTERVAL,
            **kwargs,
        )


@pytest.fixture
def ahs_program():
    """Analogue Hamiltonian Simulation program."""
    separation = 5e-6
    block_separation = 15e-6
    k_max = 5
    m_max = 5

    register = AtomArrangement()
    for k in range(k_max):
        for m in range(m_max):
            register.add((block_separation * m, block_separation * k + separation / np.sqrt(3)))
            register.add(
                (
                    block_separation * m - separation / 2,
                    block_separation * k - separation / (2 * np.sqrt(3)),
                )
            )
            register.add(
                (
                    block_separation * m + separation / 2,
                    block_separation * k - separation / (2 * np.sqrt(3)),
                )
            )

    omega_const = 1.5e7  # rad/s
    rabi_pulse_area = np.pi / np.sqrt(3)  # rad
    omega_slew_rate_max = float(
        PARADIGM["rydberg"]["rydbergGlobal"]["rabiFrequencySlewRateMax"]
    )  # rad/s^2
    time_separation_min = float(PARADIGM["rydberg"]["rydbergGlobal"]["timeDeltaMin"])  # s

    amplitude = TimeSeries.trapezoidal_signal(
        rabi_pulse_area,
        omega_const,
        0.99 * omega_slew_rate_max,
        time_separation_min=time_separation_min,
    )

    detuning = TimeSeries.constant_like(amplitude, 0.0)
    phase = TimeSeries.constant_like(amplitude, 0.0)

    drive = DrivingField(amplitude=amplitude, detuning=detuning, phase=phase)
    ahs_program = AnalogHamiltonianSimulation(register=register, hamiltonian=drive)

    return ahs_program


@pytest.fixture
def ahs_result() -> AnalogHamiltonianSimulationQuantumTaskResult:
    """Mock Analog Hamiltonian Simulation task result."""
    task_metadata = TaskMetadata(**{"id": TASK_ARN, "deviceId": AQUILA_ARN, "shots": 100})
    additional_metadata = AdditionalMetadata(
        action=Program(
            setup={
                "ahs_register": {
                    "sites": [
                        [0.0, 0.0],
                        [0.0, 3.0e-6],
                        [0.0, 6.0e-6],
                        [3.0e-6, 0.0],
                        [3.0e-6, 3.0e-6],
                        [3.0e-6, 6.0e-6],
                    ],
                    "filling": [1, 1, 1, 1, 0, 0],
                }
            },
            hamiltonian={
                "drivingFields": [
                    {
                        "amplitude": {
                            "time_series": {
                                "values": [0.0, 2.51327e7, 2.51327e7, 0.0],
                                "times": [0.0, 3.0e-7, 2.7e-6, 3.0e-6],
                            },
                            "pattern": "uniform",
                        },
                        "phase": {
                            "time_series": {"values": [0, 0], "times": [0.0, 3.0e-6]},
                            "pattern": "uniform",
                        },
                        "detuning": {
                            "time_series": {
                                "values": [-1.25664e8, -1.25664e8, 1.25664e8, 1.25664e8],
                                "times": [0.0, 3.0e-7, 2.7e-6, 3.0e-6],
                            },
                            "pattern": "uniform",
                        },
                    }
                ],
                "localDetuning": [
                    {
                        "magnitude": {
                            "time_series": {
                                "values": [-1.25664e8, 1.25664e8],
                                "times": [0.0, 3.0e-6],
                            },
                            "pattern": [0.5, 1.0, 0.5, 0.5, 0.5, 0.5],
                        }
                    }
                ],
            },
        )
    )

    success_measurement = AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Success"),
        shotResult=AnalogHamiltonianSimulationShotResult(
            preSequence=[1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            postSequence=[0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0],
        ),
    )

    success_measurement_extended = AnalogHamiltonianSimulationShotMeasurement(
        shotMetadata=AnalogHamiltonianSimulationShotMetadata(shotStatus="Success"),
        shotResult=AnalogHamiltonianSimulationShotResult(
            preSequence=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            postSequence=[1, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1],
        ),
    )

    measurements_extended = [success_measurement, success_measurement_extended]

    result = AnalogHamiltonianSimulationTaskResult(
        taskMetadata=task_metadata,
        additionalMetadata=additional_metadata,
        measurements=measurements_extended,
    )

    task_result = AnalogHamiltonianSimulationQuantumTaskResult.from_object(result)

    return task_result


@pytest.fixture
def aquila_profile():
    """Runtime profile for the device."""
    provider = BraketProvider()
    device = MockAquilaDevice()
    return provider._build_runtime_profile(device=device)


def test_aquila_runtime_profile(aquila_profile: TargetProfile):
    """Test building a runtime profile."""
    assert aquila_profile.device_id == METADATA["deviceArn"]
    assert aquila_profile.simulator is False if METADATA["deviceType"] == "QPU" else True
    assert aquila_profile.provider_name == METADATA["providerName"]


@pytest.mark.parametrize(
    "device_status, is_available, expected_status",
    [
        ("ONLINE", True, DeviceStatus.ONLINE),
        ("ONLINE", False, DeviceStatus.UNAVAILABLE),
        ("RETIRED", None, DeviceStatus.RETIRED),
        ("OFFLINE", None, DeviceStatus.OFFLINE),
    ],
)
def test_aquila_device_status(device_status, is_available, expected_status, aquila_profile):
    """Test getting Braket device status."""
    with patch("qbraid.runtime.aws.device.AwsDevice") as mock_aws_device:
        mock_aws_device_instance = mock_aws_device.return_value
        mock_aws_device_instance.status = device_status
        mock_aws_device_instance.is_available = is_available
        device = BraketDevice(profile=aquila_profile, session=MockAwsSession())
        assert device.status() == expected_status


@pytest.mark.parametrize(
    "quantum_tasks, expected_output",
    [
        ({"Normal": 5, "Priority": 3}, 8),
        ({"Normal": ">10", "Priority": "2"}, 12),
        ({"Normal": "4", "Priority": ">5"}, 9),
        ({"Normal": 0, "Priority": 0}, 0),
    ],
)
def test_queue_depth(quantum_tasks, expected_output, aquila_profile):
    """Test getting the number of jobs in the queue for the Braket device."""
    with patch("qbraid.runtime.aws.device.AwsDevice") as mock_aws_device:
        mock_aws_device_instance = mock_aws_device.return_value
        mock_queue_depth_info = MagicMock()
        mock_queue_depth_info.quantum_tasks = quantum_tasks
        mock_aws_device_instance.queue_depth.return_value = mock_queue_depth_info
        device = BraketDevice(profile=aquila_profile, session=MockAwsSession())
        assert device.queue_depth() == expected_output


def test_aquila_device_submit(aquila_profile, ahs_program):
    """Test getting a Braket device."""
    with patch("braket.aws.aws_quantum_task.AwsQuantumTask.state", return_value="COMPLETED"):
        device = BraketDevice(profile=aquila_profile, session=MockAwsSession())
        device._device = MockAquilaDevice()
        task = device.submit(ahs_program, shots=100)
        assert isinstance(task, BraketQuantumTask), f"Expected BraketQuantumTask, got {type(task)}"
        assert task.status().name == "COMPLETED"
        assert task.id == TASK_ARN


@patch("qbraid.runtime.aws.device.AwsDevice")
@patch("braket.ahs.analog_hamiltonian_simulation.AnalogHamiltonianSimulation.discretize")
def test_transform_ahs_programs(mock_aws_device, mock_discretize, aquila_profile, ahs_program):
    """Test transform method for device with AHS action type."""
    mock_aws_device.return_value = Mock()
    device = BraketDevice(aquila_profile)
    device.transform(ahs_program)
    mock_discretize.assert_called_once()


@patch("qbraid.runtime.aws.device.AwsDevice")
def test_transform_raises_for_mismatch(mock_aws_device, ahs_program):
    """Test raising exception for mismatched action type OPENQASM and program type AHS."""
    mock_aws_device.return_value = Mock()
    profile = TargetProfile(
        simulator=False,
        num_qubits=256,
        program_spec=ProgramSpec(AnalogHamiltonianSimulation, alias="braket_ahs"),
        provider_name="QuEra",
        device_id=AQUILA_ARN,
        experiment_type=ExperimentType.GATE_MODEL,
    )
    device = BraketDevice(profile)
    with pytest.raises(DeviceProgramTypeMismatchError):
        device.transform(ahs_program)


def test_get_counts_no_measurements():
    """Test getting counts with no measurements."""
    mock_result = MagicMock()
    mock_result.measurements = []
    job_result = BraketAhsResultBuilder(mock_result)
    counts = job_result.get_counts()
    assert counts is None


def test_get_counts(ahs_result):
    """Test getting counts from an AHS job result."""
    result = BraketAhsResultBuilder(ahs_result)
    counts = result.get_counts()
    expected_counts = {"rrrgeggrrgr": 1, "grggrgrrrrg": 1}
    assert counts == expected_counts


def test_get_counts_error():
    """Test getting counts from an AHS job result."""
    with patch(
        "qbraid.runtime.aws.result_builder.BraketAhsResultBuilder.measurements"
    ) as mock_measurements:
        mock_measurement = Mock()
        mock_measurement.status.name = "SUCCESS"
        del mock_measurement.pre_sequence
        mock_measurement.post_sequence = [0]

        mock_measurements.return_value = [mock_measurement]
        result = BraketAhsResultBuilder(Mock())

        with pytest.raises(ResultDecodingError):
            result.get_counts()
