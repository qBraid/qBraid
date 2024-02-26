# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: skip-file

"""
Mdule submiting and managing jobs through IBM and IBM backends.

.. currentmodule:: qbraid.providers.ibm

Classes
--------

.. autosummary::
   :toctree: ../stubs/

   QiskitBackend
   QiskitJob
   QiskitRemoteService
   QiskitProvider
   QiskitRuntime
   QiskitResult

"""
from .device import QiskitBackend
from .job import QiskitJob
from .provider import QiskitProvider, QiskitRemoteService, QiskitRuntime
from .result import QiskitResult
