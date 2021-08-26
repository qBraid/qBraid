"""
======================================================
 Braket Transpiler  (:mod:`qbraid.transpiler.braket`)
======================================================

.. currentmodule:: qbraid.transpiler.braket

Wrapping Strategy
------------------

The braket ``Moments`` data structure keeps track of when qubits should be placed
in the circuit, but does not stored individual instructions within dedicated
moment objects. Therefore, the circuits are wrapped using circuits.

Without dedicated abstract parameters, much of the complexity of wrapping
braket circuits is reduced.

Output Strategy
----------------

Braket cannot acommodate abstract parameters. Trying to transpile a parametrized
circuit to Braket will yield an error.

.. autosummary::
   :toctree: ../stubs/

   BraketGateWrapper
   BraketCircuitWrapper

"""
from .circuit import BraketCircuitWrapper
from .gate import BraketGateWrapper
