"""
==================================================================
 Braket Transpiler2  (:mod:`qbraid.transpiler2.interface.braket`)
==================================================================

.. currentmodule:: qbraid.transpiler2.interface.braket

Wrapping Strategy
------------------

The braket ``Moments`` data structure keeps track of when qubits should be placed in the circuit,
but does not stored individual instructions within dedicated moment objects. Therefore, the
circuits are wrapped using circuits.

Without dedicated abstract parameters, much of the complexity of wrapping braket circuits is
reduced.

Output Strategy
----------------

Braket cannot acommodate abstract parameters. Trying to transpile a parametrized circuit to Braket
will yield an error.

.. autosummary::
   :toctree: ../stubs/

   BraketCircuitWrapper
   from_braket
   to_braket

"""
from qbraid.transpiler2.interface.braket.convert_from_braket import from_braket
from qbraid.transpiler2.interface.braket.convert_to_braket import to_braket

from .circuit_wrapper import BraketCircuitWrapper
