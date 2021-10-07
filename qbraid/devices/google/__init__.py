"""
========================================================
Google Devices Interface (:mod:`qbraid.devices.google`)
========================================================

.. currentmodule:: qbraid.devices.google

This module contains the classes used to run quantum circuits on devices available through Google.

.. autosummary::
   :toctree: ../stubs/

   CirqSimulatorWrapper
   CirqResultWrapper

"""
# pylint: skip-file
from .localdevice import CirqSimulatorWrapper
from .result import CirqResultWrapper
