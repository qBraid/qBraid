# pylint: skip-file

import os
from braket.devices import LocalSimulator


aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")

AWS_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("aws_access_key_id", "AWS Access Key ID", None, True, "default", aws_cred_path),
    ("aws_secret_access_key", "AWS Secret Access Key", None, True, "default", aws_cred_path),
    ("region", "Default region name", "us-east-1", False, "default", aws_config_path),
    ("output", "Default output format", "json", False, "default", aws_config_path),
    ("bucket", "S3 Bucket", None, False, "s3_location", aws_config_path),
    ("folder", "S3 Bucket Folder", None, False, "s3_location", aws_config_path),
]


AWS_DEVICES = {
    "simulator_statevector": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    "simulator_densitymatrix": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
    "simulator_tensornetwork": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
    "local_simulator_default": LocalSimulator(backend="default"),
    "local_simulator_densitymatrix": "braket_dm",
    "local_simulator_statevector": "braket_sv",
}

DWAVE_DEVICES = {
    "DW_2000Q_6": "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
    "Advantage_system1": "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
}

IONQ_DEVICES = {
    "ionQdevice": "arn:aws:braket:::device/qpu/ionq/ionQdevice",
}

RIGETTI_DEVICES = {
    "Aspen-9": "arn:aws:braket:::device/qpu/rigetti/Aspen-9",
}

BRAKET_PROVIDERS = {
    "AWS": AWS_DEVICES,
    "D-Wave": DWAVE_DEVICES,
    "IonQ": IONQ_DEVICES,
    "Rigetti": RIGETTI_DEVICES,
}
