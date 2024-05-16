# Copyright (C) 2024 qBraid
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
import logging
import os
from typing import Optional

from qbraid_core import QbraidSession
from qbraid_core.services.quantum.proxy_braket import aws_configure

# Skip tests if IBM/AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid storage)"

logger = logging.getLogger(__name__)


def qbraid_configure(api_key: Optional[str] = None) -> None:
    """Initializes qBraid configuration and credentials files."""
    api_key = api_key or os.getenv("QBRAID_API_KEY", "MYAPIKEY")
    session = QbraidSession(api_key=api_key)
    session.save_config()


def ibm_configure(
    token: Optional[str] = None, channel: Optional[str] = None, overwrite: bool = True, **kwargs
) -> None:
    """Initializes IBM Quantum configuration and credentials files."""
    # pylint: disable-next=import-outside-toplevel
    from qiskit_ibm_runtime import QiskitRuntimeService

    token = token or os.getenv("QISKIT_IBM_TOKEN", "MY_IBM_QUANTUM_TOKEN")
    channel = channel or os.getenv("QISKIT_IBM_CHANNEL", "ibm_quantum")
    QiskitRuntimeService.save_account(token=token, channel=channel, overwrite=overwrite, **kwargs)


if __name__ == "__main__":
    if not skip_remote_tests:
        qbraid_configure()
        aws_configure()
        try:
            ibm_configure()
        except ImportError:
            logger.error("qiskit-ibm-runtime not installed, skipping IBM Quantum configuration")
