# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
OpenQASM conversions

.. currentmodule:: qbraid.transpiler.conversions.openqasm3

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   qasm2_to_qasm3
   openqasm3_to_qasm3
   qasm3_to_openqasm3

"""
from qbraid.transpiler.conversions.openqasm3.convert_qasm import (
    openqasm3_to_qasm3,
    qasm2_to_qasm3,
    qasm3_to_openqasm3,
)
