"""
====================================
 Interface (:mod:`qbraid.interface`)
====================================

.. currentmodule:: qbraid.interface


Interface API
--------------

.. autosummary::
   :toctree: ../stubs/

   to_unitary
   convert_to_contiguous
   random_circuit

"""
from .calculate_unitary import to_unitary
from .convert_to_contiguous import convert_to_contiguous
from .qbraid_random_circuit import random_circuit