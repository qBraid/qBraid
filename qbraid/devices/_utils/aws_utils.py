# pylint: skip-file

import os

from braket.devices import LocalSimulator

from .user_config import qbraid_config_path

aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")

AWS_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("aws_access_key_id", "AWS Access Key ID", None, True, "default", aws_cred_path),
    ("aws_secret_access_key", "AWS Secret Access Key", None, True, "default", aws_cred_path),
    ("region", "Region name (optional)", "us-east-1", False, "default", aws_config_path),
    ("output", "Output format (optional)", "json", False, "default", aws_config_path),
    ("s3_bucket", "S3 Bucket", None, False, "AWS", qbraid_config_path),
    ("s3_folder", "S3 Bucket Folder", None, False, "AWS", qbraid_config_path),
    ("verify", "", "True", False, "AWS", qbraid_config_path),
]


AWS_DEVICES = {
    "aws_braket_default_sim": LocalSimulator(backend="default"),
    "aws_dm_sim": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
    "aws_sv_sim": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
    "aws_tn_sim": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
    "aws_dwave_advantage_system1": "arn:aws:braket:::device/qpu/d-wave/Advantage_system1",
    "aws_dwave_2000Q_6": "arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6",
    "aws_ionq": "arn:aws:braket:::device/qpu/ionq/ionQdevice",
    "aws_rigetti_aspen_9": "arn:aws:braket:::device/qpu/rigetti/Aspen-9",
    # "local_simulator_densitymatrix": "braket_dm",  # not available
    # "local_simulator_statevector": "braket_sv",    # not available
}
