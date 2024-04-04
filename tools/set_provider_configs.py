# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Set config inside testing virtual environments with default values
hard-coded and secret values read from environment variables.

Note: this script is intended for CI/CD purposes only.

"""
import os
from pathlib import Path
from typing import Optional

from qbraid_core import QbraidSession
from qiskit_ibm_provider import IBMProvider

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid storage)"


def qbraid_configure(api_key: Optional[str] = None) -> None:
    """Initializes qBraid configuration and credentials files."""
    api_key = api_key or os.getenv("QBRAID_API_KEY", "MYAPIKEY")
    session = QbraidSession(api_key=api_key)
    session.save_config()


def ibm_configure(token: Optional[str] = None) -> None:
    """Initializes IBM Quantum configuration and credentials files."""
    token = token or os.getenv("QISKIT_IBM_TOKEN", "MYTOKEN")
    IBMProvider.save_account(token=token)


def aws_configure(
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    region: Optional[str] = None,
) -> None:
    """Initializes AWS configuration and credentials files."""
    aws_dir = Path.home() / ".aws"
    config_path = aws_dir / "config"
    credentials_path = aws_dir / "credentials"
    aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID", "MYACCESSKEY")
    aws_secret_access_key = aws_secret_access_key or os.getenv(
        "AWS_SECRET_ACCESS_KEY", "MYSECRETKEY"
    )
    region = region or os.getenv("AWS_REGION", "us-east-1")

    aws_dir.mkdir(exist_ok=True)
    if not config_path.exists():
        config_content = f"[default]\nregion = {region}\noutput = json\n"
        config_path.write_text(config_content)
    if not credentials_path.exists():
        credentials_content = (
            f"[default]\n"
            f"aws_access_key_id = {aws_access_key_id}\n"
            f"aws_secret_access_key = {aws_secret_access_key}\n"
        )
        credentials_path.write_text(credentials_content)


if __name__ == "__main__":
    if not skip_remote_tests:
        qbraid_configure()
        aws_configure()
        ibm_configure()
