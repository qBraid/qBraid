# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: skip-file

"""
Module that stores dictionaires containing info on how to prompt
and/or set necessary configs for each vendor.

"""

import os

aws_cred_path = os.path.join(os.path.expanduser("~"), ".aws", "credentials")
aws_config_path = os.path.join(os.path.expanduser("~"), ".aws", "config")
qiskitrc_path = os.path.join(os.path.expanduser("~"), ".qiskit", "qiskitrc")
qbraidrc_path = os.path.join(os.path.expanduser("~"), ".qbraid", "qbraidrc")

ibmq_account_url = "https://auth.quantum-computing.ibm.com/api"

# qbraid_api_url = "http://localhost:3001/api"
# qbraid_api_url = "https://api-staging.qbraid.com/api"
# qbraid_api_url_URL = "https://api.qbraid.com/api"
qbraid_api_url = "https://api-staging-1.qbraid.com/api"

AWS_CONFIGS = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("aws_access_key_id", "AWS Access Key ID", None, True, "default", aws_cred_path),
    ("aws_secret_access_key", "AWS Secret Access Key", None, True, "default", aws_cred_path),
    ("region", "Region name (optional)", "us-east-1", False, "default", aws_config_path),
    ("output", "Output format (optional)", "json", False, "default", aws_config_path),
]

IBMQ_CONFIGS = [
    # (config_name, prompt_text, default_value, is_secret, section, filepath)
    ("token", "Qiskit IBM Token", os.getenv("QISKIT_IBM_TOKEN"), True, "ibmq", qiskitrc_path),
    ("url", "", ibmq_account_url, False, "ibmq", qiskitrc_path),
    ("verify", "", "True", False, "ibmq", qiskitrc_path),
    ("default_provider", "IBMQ hub/group/name", "ibm-q/open/main", False, "ibmq", qiskitrc_path),
]

QBRAID_CONFIGS = [
    ("url", "", qbraid_api_url, False, "default", qbraidrc_path),
    ("email", "", os.getenv("JUPYTERHUB_USER"), False, "default", qbraidrc_path),
    ("id-token", "", None, False, "default", qbraidrc_path),
    ("refresh-token", "", None, False, "default", qbraidrc_path),
]

VENDOR_CONFIGS = {
    "AWS": AWS_CONFIGS,
    "Google": None,
    "IBM": IBMQ_CONFIGS,
    "QBRAID": QBRAID_CONFIGS,
}

CONFIG_PATHS = {
    "AWS": {"config": aws_config_path, "credentials": aws_cred_path},
    "IBM": {"qiskitrc": qiskitrc_path},
    "QBRAID": {"qbraidrc": qbraidrc_path},
}
