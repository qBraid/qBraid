# pylint: skip-file

import os

qbraid_config_path = os.path.join(os.path.expanduser("~"), ".qbraid", "config")
aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")
ibmq_config_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
ibmq_account_url = "https://auth.quantum-computing.ibm.com/api"

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

IBMQ_CONFIG_PROMPT = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "IBMQ API Token", None, True, "ibmq", ibmq_config_path),
    ("url", "", ibmq_account_url, False, "ibmq", ibmq_config_path),
    ("verify", "", "True", False, "ibmq", ibmq_config_path),
    ("group", "Group name (optional)", "open", False, "IBM", qbraid_config_path),
    ("project", "Project name (optional)", "main", False, "IBM", qbraid_config_path),
    ("verify", "", "True", False, "IBM", qbraid_config_path),
]

CONFIG_PROMPTS = {
    "AWS": AWS_CONFIG_PROMPT,
    "Google": None,
    "IBM": IBMQ_CONFIG_PROMPT,
}
