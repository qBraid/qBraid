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
AWS Devices Interface (:mod:`qbraid.providers.aws`)
====================================================

.. currentmodule:: qbraid.providers.aws

This module contains the classes used to run quantum circuits on devices available through AWS.

.. autosummary::
   :toctree: ../stubs/

   BraketDevice
   BraketProvider
   BraketQuantumTask
   BraketGateModelResult

"""
from .result import BraketGateModelResult
from .device import BraketDevice
from .job import BraketQuantumTask
from .provider import BraketProvider
