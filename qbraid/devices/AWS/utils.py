from braket.aws import AwsDevice
from braket.devices import LocalSimulator

SUPPORTED_DEVICES = {
    'DW_2000Q_6': AwsDevice('arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6'),
    'Advantage_system1': AwsDevice('arn:aws:braket:::device/qpu/d-wave/Advantage_system1'),
    'ionQdevice': AwsDevice('arn:aws:braket:::device/qpu/ionq/ionQdevice'),
    'Aspen-9': AwsDevice('arn:aws:braket:::device/qpu/rigetti/Aspen-9'),
    'SV1': AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/sv1'),
    'DM1': AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/dm1'),
    'TN1': AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/tn1'),
    'braket_sv': LocalSimulator(backend="braket_sv"),
    'braket_dm': LocalSimulator(backend="braket_dm"),
    'default': LocalSimulator(backend="default"),
}
