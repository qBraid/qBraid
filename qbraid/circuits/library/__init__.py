"""
=================================================
Circuit Library (:mod:`qbraid.circuits.library`)
=================================================

.. currentmodule:: qbraid.circuits.library

Standard Gates
---------------

The circuits library module for standard gates.

.. autosummary::
   :toctree: ../stubs/

   DCX
   H
   CH
   HPow
   I
   iSwap
   Measure
   Phase
   CPhase
   pSwap
   R
   RX
   RXX
   RXY
   RY
   RYY
   RZ
   RZZ
   RZX
   S
   Sdg
   Swap
   SX
   SXdg
   T
   Tdg
   U
   U1
   U2
   U3
   X
   CX
   XPow
   Y
   CY
   YPow
   CZ
   Z
   ZPow

Generalized Gates
------------------

The circuits library module for generalized gates.

.. autosummary::
   :toctree: ../stubs/

   RV
   Unitary

"""
from .generalized_gates import RV, Unitary
from .standard_gates import *
