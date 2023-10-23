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
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

.. _data_types:

Data Types
-----------

.. autodata:: QPROGRAM
   :annotation: = Type alias defining all supported quantum circuit / program types

.. autodata:: QDEVICE
   :annotation: = Type alias defining all supported quantum device / backend types

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   get_devices
   refresh_devices
   circuit_wrapper
   device_wrapper
   job_wrapper
   get_jobs

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError
   PackageValueError
   ProgramTypeError
   VisualizationError
   QasmError

"""
from . import _warnings
from ._qdevice import QDEVICE, QDEVICE_TYPES
from ._qprogram import QPROGRAM, QPROGRAM_LIBS, QPROGRAM_TYPES
from ._version import __version__
from .exceptions import (
    PackageValueError,
    ProgramTypeError,
    QasmError,
    QbraidError,
    VisualizationError,
)
from .get_devices import get_devices, refresh_devices
from .get_jobs import get_jobs
from .load_program import circuit_wrapper
from .load_provider import device_wrapper, job_wrapper
