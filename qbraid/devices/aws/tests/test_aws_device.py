from unittest.mock import Mock
from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.device_schema.rigetti import RigettiDeviceCapabilities

RIGETTI_ARN = "arn:aws:braket:::device/qpu/rigetti/Aspen-10"
RIGETTI_REGION = "us-west-1"

MOCK_DEFAULT_S3_DESTINATION_FOLDER = (
    "amazon-braket-us-test-1-00000000",
    "tasks",
)

MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_1 = {
    "braketSchemaHeader": {
        "name": "braket.device_schema.rigetti.rigetti_device_capabilities",
        "version": "1",
    },
    "service": {
        "executionWindows": [
            {
                "executionDay": "Everyday",
                "windowStartHour": "11:00",
                "windowEndHour": "12:00",
            }
        ],
        "shotsRange": [1, 10],
    },
    "action": {
        "braket.ir.jaqcd.program": {
            "actionType": "braket.ir.jaqcd.program",
            "version": ["1"],
            "supportedOperations": ["H"],
        }
    },
    "paradigm": {
        "qubitCount": 30,
        "nativeGateSet": ["ccnot", "cy"],
        "connectivity": {"fullyConnected": False, "connectivityGraph": {"1": ["2", "3"]}},
    },
    "deviceParameters": {},
}

MOCK_GATE_MODEL_QPU_CAPABILITIES_1 = RigettiDeviceCapabilities.parse_obj(
    MOCK_GATE_MODEL_QPU_CAPABILITIES_JSON_1
)

MOCK_GATE_MODEL_QPU_1 = {
    "deviceName": "Aspen-10",
    "deviceType": "QPU",
    "providerName": "provider1",
    "deviceStatus": "OFFLINE",
    "deviceCapabilities": MOCK_GATE_MODEL_QPU_CAPABILITIES_1.json(),
}

def aws_session():
    _boto_session = Mock()
    _boto_session.region_name = RIGETTI_REGION
    _boto_session.profile_name = "test-profile"

    creds = Mock()
    creds.method = "other"
    _boto_session.get_credentials.return_value = creds

    _aws_session = Mock()
    _aws_session.boto_session = _boto_session
    _aws_session._default_bucket = MOCK_DEFAULT_S3_DESTINATION_FOLDER[0]
    _aws_session.default_bucket.return_value = _aws_session._default_bucket
    _aws_session._custom_default_bucket = False
    _aws_session.account_id = "00000000"
    _aws_session.region = RIGETTI_REGION
    return _aws_session


def aws_device(arn, aws_session):
    aws_session.get_device.return_value = MOCK_GATE_MODEL_QPU_1
    aws_session.search_devices.return_value = [MOCK_GATE_MODEL_QPU_1]
    return AwsDevice(arn, aws_session)


session = aws_session()
arn = RIGETTI_ARN

device = aws_device(arn, session)

circuit = Circuit().h(1).cnot(1, 0)
print(circuit)

print(type(device))

print()

job = device.run(circuit, shots=10)
print(type(job))

print(job.metadata())
print(job.metadata()["status"])
