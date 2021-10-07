"""
==================================================
IBM Devices Interface (:mod:`qbraid.devices.ibm`)
==================================================

.. currentmodule:: qbraid.devices.ibm

This module contains the classes used to run quantum circuits on devices available through IBM.

.. autosummary::
   :toctree: ../stubs/

   QiskitBackendWrapper
   QiskitJobWrapper
   QiskitResultWrapper

"""
# pylint: skip-file
from .device import QiskitBackendWrapper
from .localdevice import QiskitBasicAerWrapper
from .job import QiskitJobWrapper
from .localjob import QiskitBasicAerJobWrapper
from .result import QiskitResultWrapper
