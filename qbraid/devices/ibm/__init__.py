"""
==================================================
IBM Devices Interface (:mod:`qbraid.devices.ibm`)
==================================================

.. currentmodule:: qbraid.devices.ibm

This module contains the classes used to run quantum circuits on devices available through IBM.

.. autosummary::
   :toctree: ../stubs/

   QiskitBackendWrapper
   QiskitBasicAerWrapper
   QiskitJobWrapper
   QiskitBasicAerJobWrapper
   QiskitResultWrapper

"""
# pylint: skip-file
from .result import QiskitResultWrapper
from .device import QiskitBackendWrapper
from .job import QiskitJobWrapper
from .localdevice import QiskitBasicAerWrapper
from .localjob import QiskitBasicAerJobWrapper
