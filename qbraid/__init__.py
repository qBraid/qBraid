"""
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

.. _data_types:

Data Types
-----------

.. autodata:: QPROGRAM
   :annotation: = Type alias defining all supported quantum circuit / program types

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   about
   get_devices
   refresh_devices
   circuit_wrapper
   device_wrapper
   retrieve_job
   job_wrapper

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError
   PackageValueError
   ProgramTypeError

"""
from . import _warnings
from ._about import about
from ._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from ._version import __version__
from .exceptions import PackageValueError, ProgramTypeError, QbraidError
from .top_level import circuit_wrapper, device_wrapper, get_devices, refresh_devices, retrieve_job, job_wrapper
