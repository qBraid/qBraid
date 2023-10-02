# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# isort: skip_file
# pylint: skip-file

"""
====================================================
IBM Devices Interface (:mod:`qbraid.providers.ibm`)
====================================================

.. currentmodule:: qbraid.providers.ibm

This module contains the classes used to run quantum circuits on devices available through IBM.

.. autosummary::
   :toctree: ../stubs/

   QiskitBackend
   QiskitJob
   QiskitProvider
   QiskitResult

"""
from .result import QiskitResult
from .device import QiskitBackend
from .job import QiskitJob
from .provider import QiskitProvider
