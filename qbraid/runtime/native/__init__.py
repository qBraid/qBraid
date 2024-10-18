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
Module providing interface for submitting and managing
quantum jobs through (native) qBraid APIs.

.. currentmodule:: qbraid.runtime.native

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    Session
    QbraidSession
    QbraidClient
    QbraidProvider
    QbraidDevice
    QbraidJob
    QirRunner

"""
from qbraid_core import QbraidClient, QbraidSession, Session
from qbraid_core.services.quantum.runner import QirRunner

from .device import QbraidDevice
from .job import QbraidJob
from .provider import QbraidProvider

__all__ = [
    "Session",
    "QbraidSession",
    "QbraidClient",
    "QbraidProvider",
    "QbraidDevice",
    "QbraidJob",
    "QirRunner",
]
