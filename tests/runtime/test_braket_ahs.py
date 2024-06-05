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
Unit tests for submitting a Braket AHS job.

"""
import json

import pytest
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.ahs.atom_arrangement import AtomArrangement
from braket.ahs.hamiltonian import Hamiltonian
from braket.device_schema.quera.quera_device_capabilities_v1 import QueraDeviceCapabilities
from braket.devices import Devices, LocalSimulator

# from decimal import Decimal
# from braket.device_schema.quera.quera_ahs_paradigm_properties_v1 import QueraAhsParadigmProperties
# QueraAhsParadigmProperties(**PARADIGM)

AQUILA_ARN = Devices.QuEra.Aquila

device = LocalSimulator("braket_ahs")

PARADIGM = (
    {
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
    },
)

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
        "deviceDocumentation": {
            "imageUrl": "https://a.b.cdn.console.awsstatic.com/59534b58c709fc239521ef866db9ea3f1aba73ad3ebcf60c23914ad8c5c5c878/a6cfc6fca26cf1c2e1c6.png",
            "summary": "Analog quantum processor based on neutral atom arrays",
            "externalDocumentationUrl": "https://www.quera.com/aquila",
        },
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
    "ResponseMetadata": {
        "RequestId": "06dd2c30-d178-4c39-94cb-5d6847b3d0e5",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "date": "Tue, 04 Jun 2024 23:27:54 GMT",
            "content-type": "application/json",
            "content-length": "4147",
            "connection": "keep-alive",
            "x-amzn-requestid": "06dd2c30-d178-4c39-94cb-5d6847b3d0e5",
            "access-control-allow-origin": "*",
            "strict-transport-security": "max-age=63072000; includeSubDomains; preload",
            "access-control-allow-headers": "*,authorization,date,x-amz-date,x-amz-security-token,x-amz-target,content-type,x-amz-content-sha256,x-amz-user-agent,x-amzn-platform-id,x-amzn-trace-id",
            "x-amz-apigw-id": "Y3ZnGEd-IAMErIA=",
            "access-control-allow-methods": "OPTIONS,GET,PUT,POST,DELETE",
            "access-control-expose-headers": "x-amzn-errortype,x-amzn-requestid,x-amzn-errormessage,x-amzn-trace-id,x-amz-apigw-id,date",
            "x-amzn-trace-id": "Root=1-665fa2f9-0c6f6179128bb2aa61a4f415",
        },
        "RetryAttempts": 0,
    },
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


class TestAwsSession:
    """Test class for AWS session."""

    def __init__(self):
        self.region = "us-east-1"

    def get_device(self, arn):  # pylint: disable=unused-argument
        """Returns metadata for a device."""
        return METADATA


class TestAwsDevice:
    """Test class for braket device."""

    def __init__(self, arn, aws_session=None):
        self.arn = arn
        self.name = "Aquila"
        self.aws_session = aws_session or TestAwsSession()
        self.status = "ONLINE"
        self.properties = QueraDeviceCapabilities(**CAPABILITIES)
        self.is_available = True

    @staticmethod
    def get_device_region(arn):  # pylint: disable=unused-argument
        """Returns the region of a device."""
        return "us-east-1"


@pytest.fixture
def ahs_program():
    """Analogue Hamiltonian Simulation program."""
    register = AtomArrangement()
    H = Hamiltonian()

    program = AnalogHamiltonianSimulation(hamiltonian=H, register=register)

    yield program


# {'ggr': 3, 'grg': 514, 'rgg': 483}
