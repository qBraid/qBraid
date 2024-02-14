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

   about
   get_devices
   refresh_devices
   circuit_wrapper
   device_wrapper
   job_wrapper
   get_jobs
   get_program_type


Classes
--------

.. autosummary::
   :toctree: ../stubs/

   LazyLoader


Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError
   PackageValueError
   ProgramTypeError
   QasmError

"""
import sys

from . import _warnings
from ._about import about
from ._import import LazyLoader
from ._qdevice import QDEVICE, QDEVICE_TYPES
from ._qprogram import QPROGRAM, QPROGRAM_LIBS, QPROGRAM_TYPES, SUPPORTED_QPROGRAMS
from ._version import __version__
from .exceptions import PackageValueError, ProgramTypeError, QasmError, QbraidError
from .get_devices import get_devices, refresh_devices
from .get_jobs import get_jobs
from .inspector import get_program_type
from .load_program import circuit_wrapper
from .load_provider import device_wrapper, job_wrapper

# TODO: Lazy loads break docs build, so for now, only loading if sphinx is installed. However,
# this should instead be implemented as skip as sphinx config or in skip_member() in conf.py.
if "sphinx" not in sys.modules:
    # lazy load interface and visualization modules.
    interface = LazyLoader("qbraid.interface", globals())
    visualization = LazyLoader("qbraid.visualization", globals())
