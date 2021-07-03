# from braket.aws import AwsDevice
from braket.devices import LocalSimulator

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

AWS_DEVICES = {
    'SV1': None,  # AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/sv1'),
    'DM1': None,  # AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/dm1'),
    'TN1': None,  # AwsDevice('arn:aws:braket:::device/quantum-simulator/amazon/tn1'),
    'braket_sv': None,  # LocalSimulator(backend="braket_sv"),
    'braket_dm': None,  # LocalSimulator(backend="braket_dm"),
    'default': LocalSimulator(backend="default"),
}

DWAVE_DEVICES = {
    'DW_2000Q_6': None,  # AwsDevice('arn:aws:braket:::device/qpu/d-wave/DW_2000Q_6'),
    'Advantage_system1': None,  # AwsDevice('arn:aws:braket:::device/qpu/d-wave/Advantage_system1'),
}

IONQ_DEVICES = {
    'ionQdevice': None,  # AwsDevice('arn:aws:braket:::device/qpu/ionq/ionQdevice'),
}

RIGETTI_DEVICES = {
    'Aspen-9': None,  # AwsDevice('arn:aws:braket:::device/qpu/rigetti/Aspen-9'),
}

BRAKET_PROVIDERS = {
    'AWS': AWS_DEVICES,
    'D-Wave': DWAVE_DEVICES,
    'IonQ': IONQ_DEVICES,
    'Rigetti': RIGETTI_DEVICES,
}
