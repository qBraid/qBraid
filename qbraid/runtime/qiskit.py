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
Module submitting and managing jobs through IBM and IBM backends.

"""
import warnings

from .ibm import QiskitBackend, QiskitJob, QiskitRuntimeProvider

warnings.warn(
    "The 'qbraid.runtime.qiskit' module is deprecated. Please use 'qbraid.runtime.ibm' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["QiskitBackend", "QiskitJob", "QiskitRuntimeProvider"]
