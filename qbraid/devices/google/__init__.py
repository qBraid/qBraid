"""
========================================================
Google Devices Interface (:mod:`qbraid.devices.google`)
========================================================

.. currentmodule:: qbraid.devices.google

This module contains the classes used to run quantum circuits on devices available through Google.

.. autosummary::
   :toctree: ../stubs/

   CirqSimulatorWrapper
   CirqLocalJobWrapper
   CirqResultWrapper

"""
# pylint: skip-file
from .result import CirqResultWrapper
from .localjob import CirqLocalJobWrapper
from .localdevice import CirqSimulatorWrapper
