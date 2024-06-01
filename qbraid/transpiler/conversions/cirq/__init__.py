# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Cirq conversions

.. currentmodule:: qbraid.transpiler.conversions.cirq

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   cirq_to_braket
   cirq_to_qasm2
   cirq_to_pyquil
   cirq_to_stim
   cirq_to_pyqir

"""
from .cirq_extras import cirq_to_pyqir, cirq_to_stim
from .cirq_to_braket import cirq_to_braket
from .cirq_to_pyquil import cirq_to_pyquil
from .cirq_to_qasm2 import cirq_to_qasm2

__all__ = ["cirq_to_braket", "cirq_to_qasm2", "cirq_to_pyquil", "cirq_to_stim", "cirq_to_pyqir"]
