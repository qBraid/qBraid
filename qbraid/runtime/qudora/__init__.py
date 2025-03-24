# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for submitting and managing jobs through QUDORA and QUDORA backends.

.. currentmodule:: qbraid.runtime.qudora

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    QUDORASession
    QUDORAProvider
    QUDORABackend
    QUDORAJob

"""

from .device import QUDORABackend
from .job import QUDORAJob
from .provider import QUDORAProvider, QUDORASession

__all__ = ["QUDORASession", "QUDORAProvider", "QUDORABackend", "QUDORAJob"]
