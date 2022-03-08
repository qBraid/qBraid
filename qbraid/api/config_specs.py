# pylint: skip-file

import os

# from qiskit.providers.ibmq.api import session as ibmq_session

qbraid_config_path = os.path.join(os.path.expanduser("~"), ".qbraid", "config")
aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")
qiskitrc_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
ibmq_account_url = "https://auth.quantum-computing.ibm.com/api"

qbraidrc_path = os.path.join(os.path.expanduser("~"), ".qbraid", "qbraidrc")
# ibmq_session_path = str(ibmq_session).split(' ')[-1].replace("'>", "'").strip("'")

qbraid_api_url = "http://localhost:3001/api"
# qbraid_api_url = "https://api-staging.qbraid.com/api"
# qbraid_api_url_URL = "https://api.qbraid.com/api"
# qbraid_api_url = "https://api-staging-1.qbraid.com/api"

AWS_CONFIGS = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("aws_access_key_id", "AWS Access Key ID", None, True, "default", aws_cred_path),
    ("aws_secret_access_key", "AWS Secret Access Key", None, True, "default", aws_cred_path),
    ("region", "Region name (optional)", "us-east-1", False, "default", aws_config_path),
    ("output", "Output format (optional)", "json", False, "default", aws_config_path),
    ("s3_bucket", "S3 Bucket", None, False, "AWS", qbraid_config_path),
    ("s3_folder", "S3 Bucket Folder", None, False, "AWS", qbraid_config_path),
    ("verify", "", "True", False, "AWS", qbraid_config_path),
]

IBMQ_CONFIGS = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "IBMQ API Token", None, True, "ibmq", qiskitrc_path),
    ("url", "", ibmq_account_url, False, "ibmq", qiskitrc_path),
    ("verify", "", "True", False, "ibmq", qiskitrc_path),
    ("group", "Group name (optional)", "open", False, "IBM", qbraid_config_path),
    ("project", "Project name (optional)", "main", False, "IBM", qbraid_config_path),
    ("verify", "", "True", False, "IBM", qbraid_config_path),
]

QBRAID_CONFIGS = [
    ("url", "", qbraid_api_url, False, "QBRAID", qbraid_config_path),
    # ("ibmq_session", "", ibmq_session_path, False, "QBRAID", qbraid_config_path),
    ("verify", "", "True", False, "QBRAID", qbraid_config_path),
]

VENDOR_CONFIGS = {
    "AWS": AWS_CONFIGS,
    "Google": None,
    "IBM": [],
    "QBRAID": QBRAID_CONFIGS,
}
