# pylint: skip-file

import os

"""
If you are working with the local simulator LocalSimulator() you do not need to specify any 
S3 location. However, if you are using a managed device or any QPU devices you need to specify 
the S3 location where your results will be stored. Bucket names for Amazon Braket must always 
begin with "amazon-braket-". 

Example:
my_bucket = "amazon-braket-Your-Bucket-Name" # the name of the bucket
my_prefix = "Your-Folder-Name" # the name of the folder in the bucket
s3_folder = (my_bucket, my_prefix)

ValueError: Only the following devices are available dict_keys(['default']) (07/02/2021) 
"""

aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "cred")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")

AWS_CONFIG_PROMPT = [
    # (config_name, prompt_text, is_secret, section, filepath)
    ("aws_access_key_id", "AWS Access Key ID", True, "default", aws_cred_path),
    ("aws_secret_access_key", "AWS Secret Access Key", True, "default", aws_cred_path),
    ("region", "Default region name", False, "default", aws_config_path),
    ("output", "Default output format", False, "default", aws_config_path),
]


AWS_DEVICES = {
    "SV1": (True, 'arn:aws:braket:::device/quantum-simulator/amazon/sv1'),
    "DM1": (True, 'arn:aws:braket:::device/quantum-simulator/amazon/dm1'),
    "TN1": (True, 'arn:aws:braket:::device/quantum-simulator/amazon/tn1'),
    "braket_sv": (True, 'braket_sv'),
    "braket_dm": (True, 'braket_dm'),
    "default": (False, 'default'),
}

DWAVE_DEVICES = {
    "DW_2000Q_6": None,  # AwsDevice('arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6'),
    "Advantage_system1": None,  # AwsDevice('arn:aws:braket:::device/qpu/d-wave/Advantage_system1'),
}

IONQ_DEVICES = {
    "ionQdevice": None,  # AwsDevice('arn:aws:braket:::device/qpu/ionq/ionQdevice'),
}

RIGETTI_DEVICES = {
    "Aspen-9": None,  # AwsDevice('arn:aws:braket:::device/qpu/rigetti/Aspen-9'),
}

BRAKET_PROVIDERS = {
    "AWS": AWS_DEVICES,
    "D-Wave": DWAVE_DEVICES,
    "IonQ": IONQ_DEVICES,
    "Rigetti": RIGETTI_DEVICES,
}
